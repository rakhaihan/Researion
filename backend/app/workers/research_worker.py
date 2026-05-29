from uuid import UUID

from app.core.logging import get_logger, setup_logging
from app.db.database import AsyncSessionLocal
from app.services.job_service import JobService
from app.services.research_service import ResearchService

logger = get_logger(__name__)


async def startup(ctx) -> None:
    setup_logging()
    logger.info("Research worker started")


async def shutdown(ctx) -> None:
    logger.info("Research worker stopped")


async def run_research_job(ctx, research_id: str, job_record_id: str) -> None:
    job_service = JobService()
    research_service = ResearchService()

    async with AsyncSessionLocal() as db:
        try:
            await job_service.mark_running(db, UUID(job_record_id))
            await db.commit()
        except Exception as exc:
            await db.rollback()
            logger.exception("Failed to mark job as running: %s", exc)
            raise

    async def on_progress(step: str, progress_percentage: int) -> None:
        async with AsyncSessionLocal() as db:
            try:
                await job_service.update_progress(
                    db,
                    UUID(job_record_id),
                    step,
                    progress_percentage,
                )
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception("Failed to update job progress for step %s", step)

    try:
        async with AsyncSessionLocal() as db:
            await research_service.execute_research_workflow(
                db,
                UUID(research_id),
                on_progress=on_progress,
            )
            await job_service.mark_completed(db, UUID(job_record_id))
            await db.commit()
    except Exception as exc:
        logger.exception("Research workflow failed for research_id=%s", research_id)
        async with AsyncSessionLocal() as db:
            try:
                await job_service.mark_failed(db, UUID(job_record_id), str(exc))
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception("Failed to mark job as failed")
        raise
