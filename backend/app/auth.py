from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db import User

# --- Password hashing -------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# --- JWT token utilities ----------------------------------------------------

ALGORITHM = "HS256"


def _create_token(data: dict, expires_delta: timedelta) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    return _create_token(
        {"sub": str(user_id), "role": role, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    return _create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- FastAPI security schemes -----------------------------------------------

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# --- Legacy API-key dependencies (backward compat) --------------------------


async def admin_required(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key not in settings.admin_api_key_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin API key")
    return api_key


async def student_required(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key not in settings.student_api_key_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid student API key")
    return api_key


async def admin_or_student_required(api_key: str = Security(api_key_header)) -> Tuple[str, str]:
    """Returns (scope, key) where scope is 'admin' or 'student'."""
    settings = get_settings()
    if api_key in settings.admin_api_key_list:
        return ("admin", api_key)
    if api_key in settings.student_api_key_list:
        return ("student", api_key)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


# --- JWT-based dependencies --------------------------------------------------


async def get_current_user(
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode a JWT bearer token and return the authenticated User.

    Raises 401 if token is invalid, expired, or user is inactive.
    """
    if bearer_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(bearer_token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


async def student_jwt_required(
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Optional[User], str]:
    """Accept EITHER a JWT Bearer token OR a legacy student API key.

    Returns (user_or_None, scope) where scope is "jwt" or "apikey".
    - JWT auth: user is the authenticated User object, scope="jwt"
    - API-key auth: user is None (caller must provide user_token separately), scope="apikey"
    """
    # Try JWT first
    if bearer_token:
        payload = decode_token(bearer_token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not an access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        return (user, "jwt")

    # Fall back to API key
    settings = get_settings()
    if api_key in settings.student_api_key_list:
        return (None, "apikey")
    if api_key in settings.admin_api_key_list:
        # Admin keys also accepted on student endpoints for backward compat
        return (None, "apikey")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — provide Bearer token or X-API-Key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def admin_or_student_jwt_required(
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Optional[User], str]:
    """Accept admin API key, student JWT, or student API key.

    Returns (user_or_None, scope) where scope is "jwt", "admin", or "student".
    """
    # Try JWT first
    if bearer_token:
        payload = decode_token(bearer_token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not an access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        return (user, "jwt")

    # Fall back to API key
    settings = get_settings()
    if api_key in settings.admin_api_key_list:
        return (None, "admin")
    if api_key in settings.student_api_key_list:
        return (None, "student")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — provide Bearer token or X-API-Key",
        headers={"WWW-Authenticate": "Bearer"},
    )