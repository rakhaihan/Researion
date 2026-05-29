from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_job_service
from app.schemas.job import JobDetailResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    job_service: JobService = Depends(get_job_service),
) -> JobDetailResponse:
    job = await job_service.get_job_by_arq_id(db, job_id)
    return JobDetailResponse.model_validate(job)
