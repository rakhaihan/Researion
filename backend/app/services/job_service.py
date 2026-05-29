from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.redis import get_arq_pool
from app.db.models import (
    STEP_PROGRESS,
    JobStatus,
    ResearchJob,
    ResearchProject,
    ResearchStatus,
    ResearchStep,
)
from app.schemas.job import STEP_LABELS, ResearchProgressResponse

logger = get_logger(__name__)

STEP_TO_RESEARCH_STATUS: dict[str, ResearchStatus] = {
    ResearchStep.PLANNING.value: ResearchStatus.PLANNING,
    ResearchStep.SEARCHING.value: ResearchStatus.SEARCHING,
    ResearchStep.EVALUATING_SOURCES.value: ResearchStatus.EVALUATING,
    ResearchStep.SUMMARIZING.value: ResearchStatus.SUMMARIZING,
    ResearchStep.ANALYZING.value: ResearchStatus.ANALYZING,
    ResearchStep.CRITIQUING.value: ResearchStatus.CRITIQUING,
    ResearchStep.WRITING_REPORT.value: ResearchStatus.WRITING,
    ResearchStep.COMPLETED.value: ResearchStatus.COMPLETED,
}

ACTIVE_JOB_STATUSES = {JobStatus.QUEUED, JobStatus.RUNNING}


class JobService:
    async def enqueue_research_job(
        self,
        db: AsyncSession,
        project: ResearchProject,
    ) -> ResearchJob:
        active_job = await self.get_active_job(db, project.id)
        if active_job is not None:
            logger.info(
                "Returning existing active job %s for research %s",
                active_job.job_id,
                project.id,
            )
            return active_job

        if project.status == ResearchStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Research is already completed",
            )

        job_record = ResearchJob(
            research_id=project.id,
            status=JobStatus.QUEUED,
            current_step=ResearchStep.PLANNING.value,
            progress_percentage=0,
        )
        db.add(job_record)

        project.status = ResearchStatus.QUEUED
        project.error_message = None
        await db.flush()

        pool = await get_arq_pool()
        arq_job = await pool.enqueue_job(
            "run_research_job",
            str(project.id),
            str(job_record.id),
        )

        if arq_job is None:
            job_record.status = JobStatus.FAILED
            job_record.error_message = "Failed to enqueue background job"
            project.status = ResearchStatus.FAILED
            project.error_message = job_record.error_message
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enqueue background job",
            )

        job_record.job_id = arq_job.job_id
        await db.flush()
        await db.refresh(job_record)

        logger.info(
            "Enqueued research job arq_id=%s record_id=%s research_id=%s",
            arq_job.job_id,
            job_record.id,
            project.id,
        )
        return job_record

    async def get_active_job(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> ResearchJob | None:
        result = await db.execute(
            select(ResearchJob)
            .where(
                ResearchJob.research_id == research_id,
                ResearchJob.status.in_(ACTIVE_JOB_STATUSES),
            )
            .order_by(ResearchJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_job(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> ResearchJob | None:
        result = await db.execute(
            select(ResearchJob)
            .where(ResearchJob.research_id == research_id)
            .order_by(ResearchJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_job_by_arq_id(
        self,
        db: AsyncSession,
        job_id: str,
        user_id: UUID,
    ) -> ResearchJob:
        result = await db.execute(
            select(ResearchJob)
            .join(ResearchProject, ResearchJob.research_id == ResearchProject.id)
            .where(ResearchJob.job_id == job_id, ResearchProject.user_id == user_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        return job

    async def get_progress(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> ResearchProgressResponse:
        project_result = await db.execute(
            select(ResearchProject).where(
                ResearchProject.id == research_id,
                ResearchProject.user_id == user_id,
            )
        )
        if project_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research project not found",
            )

        job = await self.get_latest_job(db, research_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No job found for this research project",
            )

        return self._to_progress_response(job)

    async def mark_running(
        self,
        db: AsyncSession,
        job_record_id: UUID,
    ) -> ResearchJob:
        job = await self._get_job_record(db, job_record_id)
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.current_step = ResearchStep.PLANNING.value
        job.progress_percentage = STEP_PROGRESS[ResearchStep.PLANNING.value]

        project = await self._get_project(db, job.research_id)
        project.status = ResearchStatus.PLANNING
        await db.flush()
        return job

    async def update_progress(
        self,
        db: AsyncSession,
        job_record_id: UUID,
        step: str,
        progress_percentage: int | None = None,
    ) -> None:
        job = await self._get_job_record(db, job_record_id)
        percentage = progress_percentage or STEP_PROGRESS.get(step, job.progress_percentage)

        job.current_step = step
        job.progress_percentage = percentage
        job.status = JobStatus.RUNNING

        project = await self._get_project(db, job.research_id)
        project.status = STEP_TO_RESEARCH_STATUS.get(step, project.status)
        await db.flush()

        logger.info(
            "Job progress updated job_record_id=%s step=%s progress=%s",
            job_record_id,
            step,
            percentage,
        )

    async def mark_completed(
        self,
        db: AsyncSession,
        job_record_id: UUID,
    ) -> None:
        job = await self._get_job_record(db, job_record_id)
        job.status = JobStatus.COMPLETED
        job.current_step = ResearchStep.COMPLETED.value
        job.progress_percentage = STEP_PROGRESS[ResearchStep.COMPLETED.value]
        job.completed_at = datetime.now(UTC)

        project = await self._get_project(db, job.research_id)
        project.status = ResearchStatus.COMPLETED
        project.error_message = None
        await db.flush()

        logger.info("Job completed job_record_id=%s research_id=%s", job_record_id, job.research_id)

    async def mark_failed(
        self,
        db: AsyncSession,
        job_record_id: UUID,
        error_message: str,
    ) -> None:
        job = await self._get_job_record(db, job_record_id)
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(UTC)

        project = await self._get_project(db, job.research_id)
        project.status = ResearchStatus.FAILED
        project.error_message = error_message
        await db.flush()

        logger.error(
            "Job failed job_record_id=%s research_id=%s error=%s",
            job_record_id,
            job.research_id,
            error_message,
        )

    async def list_jobs_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 100,
    ) -> list[ResearchJob]:
        result = await db.execute(
            select(ResearchJob)
            .join(ResearchProject, ResearchJob.research_id == ResearchProject.id)
            .where(ResearchProject.user_id == user_id)
            .order_by(ResearchJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cleanup_old_jobs(
        self,
        db: AsyncSession,
        *,
        older_than_days: int = 30,
        statuses: tuple[JobStatus, ...] = (JobStatus.COMPLETED, JobStatus.FAILED),
    ) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        result = await db.execute(
            delete(ResearchJob).where(
                ResearchJob.status.in_(statuses),
                ResearchJob.updated_at < cutoff,
            )
        )
        deleted = result.rowcount or 0
        logger.info("Cleaned up %s old jobs older than %s days", deleted, older_than_days)
        return deleted

    def _to_progress_response(self, job: ResearchJob) -> ResearchProgressResponse:
        step = job.current_step
        return ResearchProgressResponse(
            research_id=job.research_id,
            job_id=job.job_id,
            status=job.status,
            current_step=step,
            current_step_label=STEP_LABELS.get(step, step) if step else None,
            progress_percentage=job.progress_percentage,
            error_message=job.error_message,
            started_at=job.started_at,
            updated_at=job.updated_at,
        )

    async def _get_job_record(
        self,
        db: AsyncSession,
        job_record_id: UUID,
    ) -> ResearchJob:
        result = await db.execute(
            select(ResearchJob).where(ResearchJob.id == job_record_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise ValueError(f"Research job record not found: {job_record_id}")
        return job

    async def _get_project(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> ResearchProject:
        result = await db.execute(
            select(ResearchProject).where(ResearchProject.id == research_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ValueError(f"Research project not found: {research_id}")
        return project
