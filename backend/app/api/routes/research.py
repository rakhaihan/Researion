from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_research_service
from app.schemas.job import JobStatus, ResearchProgressResponse, ResearchRunResponse
from app.schemas.research import (
    ResearchCreate,
    ResearchDetailResponse,
    ResearchSummaryResponse,
)
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    payload: ResearchCreate,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
) -> ResearchSummaryResponse:
    project = await service.create_research(db, payload)
    return ResearchSummaryResponse.model_validate(project)


@router.get("", response_model=list[ResearchSummaryResponse])
async def list_research(
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
) -> list[ResearchSummaryResponse]:
    projects = await service.list_research(db)
    return [ResearchSummaryResponse.model_validate(project) for project in projects]


@router.get("/{research_id}/progress", response_model=ResearchProgressResponse)
async def get_research_progress(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
) -> ResearchProgressResponse:
    return await service.job_service.get_progress(db, research_id)


@router.get("/{research_id}", response_model=ResearchDetailResponse)
async def get_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
) -> ResearchDetailResponse:
    project = await service.get_research(db, research_id)
    return ResearchDetailResponse.model_validate(project)


@router.post("/{research_id}/run", response_model=ResearchRunResponse)
async def run_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
) -> ResearchRunResponse:
    project, job = await service.enqueue_research_run(db, research_id)

    if job.status == JobStatus.QUEUED:
        message = "Research job queued successfully"
    elif job.status == JobStatus.RUNNING:
        message = "Research job is already running"
    else:
        message = f"Returning existing job with status: {job.status.value}"

    return ResearchRunResponse(
        research_id=project.id,
        job_id=job.job_id or "",
        status=job.status,
        message=message,
    )
