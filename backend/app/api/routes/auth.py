from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_db, resolve_current_user
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublicResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_limit():
    return get_settings().auth_rate_limit


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit(_auth_limit)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(_auth_limit)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.login(db, payload)


@router.get("/me", response_model=UserPublicResponse)
async def me(current_user: User = Depends(resolve_current_user)) -> UserPublicResponse:
    return UserPublicResponse.model_validate(current_user)
