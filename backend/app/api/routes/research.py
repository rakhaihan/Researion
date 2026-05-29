import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_research_service, resolve_current_user
from app.db.database import AsyncSessionLocal
from app.db.models import User
from app.schemas.job import JobStatus, ResearchProgressResponse, ResearchRunResponse
from app.schemas.quality import ResearchQualityEvaluationResponse
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
    current_user: User = Depends(resolve_current_user),
) -> ResearchSummaryResponse:
    project = await service.create_research(db, payload, current_user.id)
    return ResearchSummaryResponse.model_validate(project)


@router.get("", response_model=list[ResearchSummaryResponse])
async def list_research(
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> list[ResearchSummaryResponse]:
    projects = await service.list_research(db, current_user.id)
    return [ResearchSummaryResponse.model_validate(project) for project in projects]


@router.get("/{research_id}/progress", response_model=ResearchProgressResponse)
async def get_research_progress(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchProgressResponse:
    return await service.job_service.get_progress(db, research_id, current_user.id)


@router.get("/{research_id}/progress/stream")
async def stream_research_progress(
    research_id: UUID,
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> StreamingResponse:
    user_id = current_user.id

    async def event_generator():
        terminal = {JobStatus.COMPLETED, JobStatus.FAILED}
        while True:
            async with AsyncSessionLocal() as db:
                progress = await service.job_service.get_progress(db, research_id, user_id)
            payload = {
                "research_id": str(progress.research_id),
                "job_id": progress.job_id,
                "status": progress.status.value,
                "current_step": progress.current_step,
                "current_step_label": progress.current_step_label,
                "progress_percentage": progress.progress_percentage,
                "error_message": progress.error_message,
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "updated_at": progress.updated_at.isoformat(),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if progress.status in terminal:
                break
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{research_id}/quality", response_model=ResearchQualityEvaluationResponse)
async def get_research_quality(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchQualityEvaluationResponse:
    return await service.get_quality_evaluation(db, research_id, current_user.id)


@router.post("/{research_id}/regenerate-report", response_model=ResearchDetailResponse)
async def regenerate_report(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchDetailResponse:
    project = await service.regenerate_report(db, research_id, current_user.id)
    return service.to_detail_response(project)


@router.get("/{research_id}", response_model=ResearchDetailResponse)
async def get_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchDetailResponse:
    project = await service.get_research(db, research_id, user_id=current_user.id)
    return service.to_detail_response(project)


@router.post("/{research_id}/run", response_model=ResearchRunResponse)
async def run_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchRunResponse:
    project, job = await service.enqueue_research_run(db, research_id, current_user.id)

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
