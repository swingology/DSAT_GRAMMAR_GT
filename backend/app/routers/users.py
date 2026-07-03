from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import admin_required, hash_password
from app.models.db import User, UserProgress
from app.models.payload import AdminPasswordReset, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    # Normalize empty/whitespace-only email to NULL: User.email is
    # unique+nullable, so a stored "" would collide on the second empty-email
    # user (IntegrityError → 500) and defeat the admin UI's email??username
    # display fallback.
    email = (body.email or "").strip() or None
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Username already exists")
    if email:
        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalars().first():
            raise HTTPException(status_code=409, detail="Email already exists")
    user = User(username=body.username, email=email, created_at=datetime.now(timezone.utc))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    result = await db.execute(
        select(User).order_by(User.id).offset(offset).limit(limit)
    )
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided")

    if "username" in changes and changes["username"] != user.username:
        existing = await db.execute(select(User).where(User.username == changes["username"]))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Username already exists")

    if "email" in changes and changes["email"] and changes["email"] != user.email:
        existing = await db.execute(select(User).where(User.email == changes["email"]))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Email already exists")

    for field, value in changes.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: int,
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    user.refresh_token = None
    user.refresh_token_expires = None
    await db.commit()


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(delete(UserProgress).where(UserProgress.user_id == user_id))
    await db.delete(user)
    await db.commit()
