from typing import Tuple
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


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