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