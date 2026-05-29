from collections.abc import AsyncGenerator

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import api_key_header, bearer_scheme, get_current_user
from app.db.database import AsyncSessionLocal
from app.db.models import User
from app.services.auth_service import AuthService
from app.services.job_service import JobService
from app.services.research_service import ResearchService
from app.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def resolve_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
) -> User:
    return await get_current_user(db, credentials=credentials, api_key=api_key)


def get_research_service() -> ResearchService:
    return ResearchService()


def get_job_service() -> JobService:
    return JobService()


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_service() -> UserService:
    return UserService()
