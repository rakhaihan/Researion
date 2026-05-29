from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.password import hash_password
from app.db.models import User


class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        full_name: str,
        email: str,
        password: str,
        is_superuser: bool = False,
    ) -> User:
        normalized_email = email.lower().strip()
        existing = await self.get_by_email(db, normalized_email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            full_name=full_name.strip(),
            email=normalized_email,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=is_superuser,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def ensure_dev_user(self, db: AsyncSession, settings: Settings | None = None) -> User:
        settings = settings or get_settings()
        user = await self.get_by_email(db, settings.dev_user_email)
        if user is not None:
            return user
        return await self.create_user(
            db,
            full_name=settings.dev_user_full_name,
            email=settings.dev_user_email,
            password=settings.dev_user_password,
            is_superuser=True,
        )
