from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_research_service, resolve_current_user
from app.db.models import User
from app.schemas.report import FinalReportResponse
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["reports"])


@router.get("/{research_id}/report", response_model=FinalReportResponse)
async def get_report(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> FinalReportResponse:
    report = await service.get_report(db, research_id, current_user.id)
    return FinalReportResponse.model_validate(report)


@router.get("/{research_id}/export/markdown")
async def export_markdown(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> Response:
    filename, content = await service.export_markdown(db, research_id, current_user.id)
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{research_id}/export/pdf")
async def export_pdf(
    research_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ResearchService = Depends(get_research_service),
    current_user: User = Depends(resolve_current_user),
) -> Response:
    filename, pdf_bytes = await service.export_pdf(db, research_id, current_user.id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
