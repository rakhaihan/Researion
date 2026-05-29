from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_job_service, resolve_current_user
from app.api.deps_admin import require_admin_api_key
from app.db.models import User
from app.schemas.job import JobCleanupResponse, JobDetailResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobDetailResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service),
    current_user: User = Depends(resolve_current_user),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[JobDetailResponse]:
    jobs = await job_service.list_jobs_for_user(db, current_user.id, limit=limit)
    return [JobDetailResponse.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service),
    current_user: User = Depends(resolve_current_user),
) -> JobDetailResponse:
    job = await job_service.get_job_by_arq_id(db, job_id, current_user.id)
    return JobDetailResponse.model_validate(job)


@router.post("/admin/cleanup", response_model=JobCleanupResponse)
async def cleanup_old_jobs(
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service),
    _: None = Depends(require_admin_api_key),
    older_than_days: int = Query(default=30, ge=1, le=365),
) -> JobCleanupResponse:
    deleted = await job_service.cleanup_old_jobs(db, older_than_days=older_than_days)
    return JobCleanupResponse(deleted_count=deleted, older_than_days=older_than_days)
