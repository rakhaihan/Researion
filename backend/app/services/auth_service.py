from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token
from app.core.password import verify_password
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublicResponse
from app.services.user_service import UserService


class AuthService:
    def __init__(self) -> None:
        self.user_service = UserService()

    async def register(self, db: AsyncSession, payload: RegisterRequest) -> TokenResponse:
        user = await self.user_service.create_user(
            db,
            full_name=payload.full_name,
            email=str(payload.email),
            password=payload.password,
        )
        return self._build_token_response(user)

    async def login(self, db: AsyncSession, payload: LoginRequest) -> TokenResponse:
        user = await self.user_service.get_by_email(db, str(payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        token = create_access_token(str(user.id))
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserPublicResponse.model_validate(user),
        )
