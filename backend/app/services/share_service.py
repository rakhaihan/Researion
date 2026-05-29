import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.models import (
    ResearchProject,
    SharedReportLink,
    ShareVisibility,
    SourceResult,
)
from app.schemas.share import (
    PublicReportResponse,
    PublicSourceResponse,
    ShareLinkCreate,
    ShareLinkResponse,
)
from app.services.pdf_service import PDFService
from app.services.permission_service import PermissionService
from app.utils.validators import sanitize_filename


class ShareService:
    def __init__(self) -> None:
        self.permissions = PermissionService()
        self.pdf_service = PDFService()
        self.settings = get_settings()

    async def create_share_link(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
        payload: ShareLinkCreate,
    ) -> ShareLinkResponse:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        if not await self.permissions.can_share_research(db, project, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot share this research")
        if project.final_report is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No report to share")

        link = SharedReportLink(
            research_id=research_id,
            created_by=user_id,
            token=secrets.token_urlsafe(32),
            visibility=ShareVisibility(payload.visibility.value),
            expires_at=payload.expires_at,
            allow_download=payload.allow_download,
        )
        db.add(link)
        await db.flush()
        await db.refresh(link)
        return self._to_response(link)

    async def list_share_links(
        self, db: AsyncSession, research_id: UUID, user_id: UUID
    ) -> list[ShareLinkResponse]:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        result = await db.execute(
            select(SharedReportLink)
            .where(SharedReportLink.research_id == research_id)
            .order_by(SharedReportLink.created_at.desc())
        )
        return [self._to_response(link) for link in result.scalars().all()]

    async def revoke_share_link(
        self,
        db: AsyncSession,
        research_id: UUID,
        share_id: UUID,
        user_id: UUID,
    ) -> None:
        project = await self._get_project(db, research_id)
        if not await self.permissions.can_share_research(db, project, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot revoke share link")
        link = await self._get_link(db, research_id, share_id)
        link.revoked_at = datetime.now(UTC)
        await db.flush()

    async def get_public_report(self, db: AsyncSession, token: str) -> PublicReportResponse:
        link = await self._resolve_active_link(db, token)
        project = await self._load_project_with_report(db, link.research_id)
        return self._public_response(project, link.allow_download)

    async def export_public_markdown(
        self, db: AsyncSession, token: str
    ) -> tuple[str, str]:
        link = await self._resolve_active_link(db, token)
        if not link.allow_download:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Download not allowed")
        project = await self._load_project_with_report(db, link.research_id)
        report = project.final_report
        filename = f"{sanitize_filename(project.topic)}.md"
        return filename, report.markdown_content if report else ""

    async def export_public_pdf(self, db: AsyncSession, token: str) -> tuple[str, bytes]:
        link = await self._resolve_active_link(db, token)
        if not link.allow_download:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Download not allowed")
        project = await self._load_project_with_report(db, link.research_id)
        report = project.final_report
        if report is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found")
        filename = self.pdf_service.build_filename(project.topic)
        title = report.markdown_content.split("\n")[0].lstrip("# ").strip() or project.topic
        pdf_bytes = self.pdf_service.generate_pdf(
            title=title,
            markdown_content=report.markdown_content,
        )
        return filename, pdf_bytes

    async def _resolve_active_link(self, db: AsyncSession, token: str) -> SharedReportLink:
        result = await db.execute(
            select(SharedReportLink).where(SharedReportLink.token == token)
        )
        link = result.scalar_one_or_none()
        if link is None or link.revoked_at is not None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Share link not found")
        if link.expires_at and link.expires_at < datetime.now(UTC):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Share link expired")
        return link

    async def _load_project_with_report(
        self, db: AsyncSession, research_id: UUID
    ) -> ResearchProject:
        result = await db.execute(
            select(ResearchProject)
            .where(ResearchProject.id == research_id)
            .options(
                selectinload(ResearchProject.final_report),
                selectinload(ResearchProject.sources),
            )
        )
        project = result.scalar_one_or_none()
        if project is None or project.final_report is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found")
        return project

    async def _get_project(self, db: AsyncSession, research_id: UUID) -> ResearchProject:
        result = await db.execute(
            select(ResearchProject)
            .where(ResearchProject.id == research_id)
            .options(selectinload(ResearchProject.final_report))
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Research not found")
        return project

    async def _get_link(
        self, db: AsyncSession, research_id: UUID, share_id: UUID
    ) -> SharedReportLink:
        result = await db.execute(
            select(SharedReportLink).where(
                SharedReportLink.id == share_id,
                SharedReportLink.research_id == research_id,
            )
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Share link not found")
        return link

    def _public_response(
        self, project: ResearchProject, allow_download: bool
    ) -> PublicReportResponse:
        report = project.final_report
        assert report is not None
        sources = [
            PublicSourceResponse(
                citation_key=s.citation_key,
                title=self._public_source_title(s),
                source_type=s.source_type,
                page_number=s.page_number,
                snippet=(s.snippet[:300] if s.snippet else None),
            )
            for s in project.sources
        ]
        title = report.markdown_content.split("\n")[0].lstrip("# ").strip() or project.topic
        return PublicReportResponse(
            title=title,
            markdown_content=report.markdown_content,
            quality_score=project.quality_score,
            quality_status=project.quality_status.value if project.quality_status else None,
            sources=sources,
            created_at=project.created_at,
            updated_at=project.updated_at,
            allow_download=allow_download,
        )

    @staticmethod
    def _public_source_title(source: SourceResult) -> str:
        if source.source_type == "document" or str(source.url).startswith("document://"):
            page = f", page {source.page_number}" if source.page_number else ""
            return f"{source.title}{page}"
        return source.title

    def _to_response(self, link: SharedReportLink) -> ShareLinkResponse:
        base = self.settings.frontend_url.rstrip("/")
        return ShareLinkResponse(
            id=link.id,
            research_id=link.research_id,
            token=link.token,
            visibility=link.visibility,
            expires_at=link.expires_at,
            allow_download=link.allow_download,
            created_at=link.created_at,
            revoked_at=link.revoked_at,
            share_url=f"{base}/public/reports/{link.token}",
        )
