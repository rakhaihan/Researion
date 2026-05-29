from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.share import PublicReportResponse
from app.services.share_service import ShareService

router = APIRouter(prefix="/public/reports", tags=["public"])


def get_share_service() -> ShareService:
    return ShareService()


@router.get("/{token}", response_model=PublicReportResponse)
async def get_public_report(
    token: str,
    db: AsyncSession = Depends(get_db),
    service: ShareService = Depends(get_share_service),
) -> PublicReportResponse:
    return await service.get_public_report(db, token)


@router.get("/{token}/export/markdown")
async def export_public_markdown(
    token: str,
    db: AsyncSession = Depends(get_db),
    service: ShareService = Depends(get_share_service),
) -> Response:
    filename, content = await service.export_public_markdown(db, token)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{token}/export/pdf")
async def export_public_pdf(
    token: str,
    db: AsyncSession = Depends(get_db),
    service: ShareService = Depends(get_share_service),
) -> Response:
    filename, pdf_bytes = await service.export_public_pdf(db, token)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
