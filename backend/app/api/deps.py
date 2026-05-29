from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.services.job_service import JobService
from app.services.research_service import ResearchService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_research_service() -> ResearchService:
    return ResearchService()


def get_job_service() -> JobService:
    return JobService()
