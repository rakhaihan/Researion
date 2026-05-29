from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def require_admin_api_key(x_admin_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API is not configured",
        )
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )
