import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_research_service, resolve_current_user
from app.db.database import AsyncSessionLocal
from app.db.models import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.schemas.job import JobStatus, ResearchProgressResponse, ResearchRunResponse
from app.schemas.quality import ResearchQualityEvaluationResponse
from app.schemas.research import (
    ResearchCreate,
    ResearchDetailResponse,
    ResearchSummaryResponse,
)
from app.schemas.share import ShareLinkCreate, ShareLinkResponse
from app.schemas.version import ReportVersionResponse, VersionCompareResponse
from app.services.comment_service import CommentService
from app.services.research_service import ResearchService
from app.services.share_service import ShareService
from app.services.version_service import VersionService

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
    workspace_id: UUID | None = None,
    status: str | None = None,
    research_type: str | None = None,
    source_mode: str | None = None,
    pinned: bool | None = None,
    archived: bool = False,
    q: str | None = None,
    sort: str = Query(default="latest", pattern="^(latest|oldest|title)$"),
) -> list[ResearchSummaryResponse]:
    projects = await service.list_research(
        db,
        current_user.id,
        workspace_id=workspace_id,
        status=status,
        research_type=research_type,
        source_mode=source_mode,
        pinned=pinned,
        archived=archived,
        q=q,
        sort=sort,
    )
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


@router.post("/{research_id}/pin", response_model=ResearchSummaryResponse)
async def pin_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchSummaryResponse:
    project = await service.pin_research(db, research_id, current_user.id)
    return ResearchSummaryResponse.model_validate(project)


@router.post("/{research_id}/unpin", response_model=ResearchSummaryResponse)
async def unpin_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchSummaryResponse:
    project = await service.unpin_research(db, research_id, current_user.id)
    return ResearchSummaryResponse.model_validate(project)


@router.post("/{research_id}/archive", response_model=ResearchSummaryResponse)
async def archive_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchSummaryResponse:
    project = await service.archive_research(db, research_id, current_user.id)
    return ResearchSummaryResponse.model_validate(project)


@router.post("/{research_id}/restore", response_model=ResearchSummaryResponse)
async def restore_research(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> ResearchSummaryResponse:
    project = await service.restore_research(db, research_id, current_user.id)
    return ResearchSummaryResponse.model_validate(project)


@router.post("/{research_id}/share", response_model=ShareLinkResponse, status_code=201)
async def create_share_link(
    research_id: UUID,
    payload: ShareLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> ShareLinkResponse:
    return await ShareService().create_share_link(db, research_id, current_user.id, payload)


@router.get("/{research_id}/share", response_model=list[ShareLinkResponse])
async def list_share_links(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> list[ShareLinkResponse]:
    return await ShareService().list_share_links(db, research_id, current_user.id)


@router.delete("/{research_id}/share/{share_id}", status_code=204)
async def revoke_share_link(
    research_id: UUID,
    share_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> None:
    await ShareService().revoke_share_link(db, research_id, share_id, current_user.id)


@router.get("/{research_id}/versions", response_model=list[ReportVersionResponse])
async def list_versions(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> list[ReportVersionResponse]:
    return await VersionService().list_versions(db, research_id, current_user.id)


@router.get("/{research_id}/versions/compare", response_model=VersionCompareResponse)
async def compare_versions(
    research_id: UUID,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> VersionCompareResponse:
    return await VersionService().compare_versions(
        db, research_id, current_user.id, from_version, to_version
    )


@router.get("/{research_id}/versions/{version_id}", response_model=ReportVersionResponse)
async def get_version(
    research_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> ReportVersionResponse:
    return await VersionService().get_version(db, research_id, version_id, current_user.id)


@router.post(
    "/{research_id}/versions/{version_id}/restore",
    response_model=ReportVersionResponse,
)
async def restore_version(
    research_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> ReportVersionResponse:
    return await VersionService().restore_version(
        db, research_id, version_id, current_user.id
    )


@router.get("/{research_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> list[CommentResponse]:
    return await CommentService().list_comments(db, research_id, current_user.id)


@router.post("/{research_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    research_id: UUID,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> CommentResponse:
    return await CommentService().create_comment(db, research_id, current_user.id, payload)


@router.patch("/{research_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    research_id: UUID,
    comment_id: UUID,
    payload: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> CommentResponse:
    return await CommentService().update_comment(
        db, research_id, comment_id, current_user.id, payload
    )


@router.delete("/{research_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    research_id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(resolve_current_user),
) -> None:
    await CommentService().delete_comment(db, research_id, comment_id, current_user.id)


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
