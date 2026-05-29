import difflib
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import FinalReport, ReportVersion, ResearchProject
from app.schemas.version import ReportVersionResponse, VersionCompareResponse
from app.services.permission_service import PermissionService


class VersionService:
    def __init__(self) -> None:
        self.permissions = PermissionService()

    async def create_version_from_report(
        self,
        db: AsyncSession,
        project: ResearchProject,
        report: FinalReport,
        *,
        created_by: UUID | None = None,
        change_reason: str | None = None,
    ) -> ReportVersion:
        version_number = await self._next_version_number(db, project.id)
        version = ReportVersion(
            research_id=project.id,
            version_number=version_number,
            markdown_content=report.markdown_content,
            executive_summary=report.executive_summary,
            detailed_analysis=report.detailed_analysis,
            key_findings=report.key_findings,
            risks=report.risks,
            conclusion=report.conclusion,
            quality_score=project.quality_score,
            quality_status=project.quality_status,
            created_by=created_by,
            change_reason=change_reason,
        )
        db.add(version)
        await db.flush()
        return version

    async def list_versions(
        self, db: AsyncSession, research_id: UUID, user_id: UUID
    ) -> list[ReportVersionResponse]:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        result = await db.execute(
            select(ReportVersion)
            .where(ReportVersion.research_id == research_id)
            .order_by(ReportVersion.version_number.desc())
        )
        return [ReportVersionResponse.model_validate(v) for v in result.scalars().all()]

    async def get_version(
        self, db: AsyncSession, research_id: UUID, version_id: UUID, user_id: UUID
    ) -> ReportVersionResponse:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        version = await self._get_version(db, research_id, version_id)
        return ReportVersionResponse.model_validate(version)

    async def restore_version(
        self,
        db: AsyncSession,
        research_id: UUID,
        version_id: UUID,
        user_id: UUID,
    ) -> ReportVersionResponse:
        project = await self._get_project(db, research_id)
        if not await self.permissions.can_edit_research(db, project, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot restore version")
        version = await self._get_version(db, research_id, version_id)
        if project.final_report is None:
            project.final_report = FinalReport(research_id=project.id)
            db.add(project.final_report)
            await db.flush()

        report = project.final_report
        report.markdown_content = version.markdown_content
        report.executive_summary = version.executive_summary
        report.detailed_analysis = version.detailed_analysis
        report.key_findings = version.key_findings
        report.risks = version.risks
        report.conclusion = version.conclusion
        project.quality_score = version.quality_score
        project.quality_status = version.quality_status
        await db.flush()

        restored = await self.create_version_from_report(
            db,
            project,
            report,
            created_by=user_id,
            change_reason=f"Restored from version {version.version_number}",
        )
        return ReportVersionResponse.model_validate(restored)

    async def compare_versions(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
        from_version: int,
        to_version: int,
    ) -> VersionCompareResponse:
        project = await self._get_project(db, research_id)
        await self.permissions.require_view_research(db, project, user_id)
        v_from = await self._get_version_by_number(db, research_id, from_version)
        v_to = await self._get_version_by_number(db, research_id, to_version)
        return self._compare(v_from, v_to)

    async def _next_version_number(self, db: AsyncSession, research_id: UUID) -> int:
        result = await db.execute(
            select(func.max(ReportVersion.version_number)).where(
                ReportVersion.research_id == research_id
            )
        )
        current = result.scalar_one_or_none() or 0
        return int(current) + 1

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

    async def _get_version(
        self, db: AsyncSession, research_id: UUID, version_id: UUID
    ) -> ReportVersion:
        result = await db.execute(
            select(ReportVersion).where(
                ReportVersion.id == version_id,
                ReportVersion.research_id == research_id,
            )
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Version not found")
        return version

    async def _get_version_by_number(
        self, db: AsyncSession, research_id: UUID, version_number: int
    ) -> ReportVersion:
        result = await db.execute(
            select(ReportVersion).where(
                ReportVersion.research_id == research_id,
                ReportVersion.version_number == version_number,
            )
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Version not found")
        return version

    @staticmethod
    def _compare(v_from: ReportVersion, v_to: ReportVersion) -> VersionCompareResponse:
        from_sections = VersionService._extract_sections(v_from.markdown_content)
        to_sections = VersionService._extract_sections(v_to.markdown_content)
        from_keys = set(from_sections)
        to_keys = set(to_sections)
        added = sorted(to_keys - from_keys)
        removed = sorted(from_keys - to_keys)
        changed = [
            key
            for key in from_keys & to_keys
            if from_sections[key].strip() != to_sections[key].strip()
        ]
        summary_parts = []
        if added:
            summary_parts.append(f"Added sections: {', '.join(added)}")
        if removed:
            summary_parts.append(f"Removed sections: {', '.join(removed)}")
        if changed:
            summary_parts.append(f"Changed sections: {', '.join(changed)}")
        diff = "\n".join(
            difflib.unified_diff(
                v_from.markdown_content.splitlines(),
                v_to.markdown_content.splitlines(),
                fromfile=f"v{v_from.version_number}",
                tofile=f"v{v_to.version_number}",
                lineterm="",
            )
        )
        return VersionCompareResponse(
            from_version=v_from.version_number,
            to_version=v_to.version_number,
            added_sections=added,
            removed_sections=removed,
            changed_summary="; ".join(summary_parts) or "No structural changes detected",
            markdown_diff=diff,
        )

    @staticmethod
    def _extract_sections(markdown: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        current = "_preamble"
        buffer: list[str] = []
        for line in markdown.splitlines():
            if line.startswith("## "):
                sections[current] = "\n".join(buffer)
                current = line[3:].strip().lower()
                buffer = []
            else:
                buffer.append(line)
        sections[current] = "\n".join(buffer)
        return sections
