from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models import (
    FinalReport,
    ResearchDepth,
    ResearchJob,
    ResearchProject,
    ResearchQuestion,
    ResearchStatus,
    ResearchType,
    SourceResult,
    SourceSummary,
)
from app.schemas.research import ResearchCreate
from app.services.job_service import JobService
from app.services.pdf_service import PDFService
from app.utils.validators import sanitize_filename, validate_topic
from app.workflows.research_graph import ResearchWorkflow

logger = get_logger(__name__)

ProgressHandler = Callable[[str, int], Awaitable[None]]


class ResearchService:
    def __init__(self) -> None:
        self._workflow: ResearchWorkflow | None = None
        self.pdf_service = PDFService()
        self.job_service = JobService()

    @property
    def workflow(self) -> ResearchWorkflow:
        if self._workflow is None:
            self._workflow = ResearchWorkflow()
        return self._workflow

    async def create_research(
        self,
        db: AsyncSession,
        payload: ResearchCreate,
    ) -> ResearchProject:
        topic = validate_topic(payload.topic)

        project = ResearchProject(
            topic=topic,
            research_type=ResearchType(payload.research_type.value),
            depth=ResearchDepth(payload.depth.value),
            status=ResearchStatus.PENDING,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    async def list_research(self, db: AsyncSession) -> list[ResearchProject]:
        result = await db.execute(
            select(ResearchProject).order_by(ResearchProject.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_research(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> ResearchProject:
        result = await db.execute(
            select(ResearchProject)
            .where(ResearchProject.id == research_id)
            .options(
                selectinload(ResearchProject.questions),
                selectinload(ResearchProject.sources).selectinload(SourceResult.summary),
                selectinload(ResearchProject.final_report),
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research project not found",
            )
        return project

    async def enqueue_research_run(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> tuple[ResearchProject, ResearchJob]:
        project = await self.get_research(db, research_id)
        job = await self.job_service.enqueue_research_job(db, project)
        await db.refresh(project)
        return project, job

    async def execute_research_workflow(
        self,
        db: AsyncSession,
        research_id: UUID,
        on_progress: ProgressHandler | None = None,
    ) -> ResearchProject:
        project = await self.get_research(db, research_id)
        await self._clear_previous_results(db, project.id)

        state = await self.workflow.run(
            topic=project.topic,
            research_type=project.research_type.value,
            depth=project.depth.value,
            on_progress=on_progress,
        )

        await self._persist_workflow_results(db, project, state)
        await db.refresh(project)
        return project

    async def get_report(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> FinalReport:
        project = await self.get_research(db, research_id)
        if project.final_report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Final report not found. Run the research workflow first.",
            )
        return project.final_report

    async def export_markdown(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> tuple[str, str]:
        report = await self.get_report(db, research_id)
        filename = f"{sanitize_filename((await self.get_research(db, research_id)).topic)}.md"
        return filename, report.markdown_content

    async def export_pdf(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> tuple[str, bytes]:
        project = await self.get_research(db, research_id)
        report = await self.get_report(db, research_id)
        filename = self.pdf_service.build_filename(project.topic)
        pdf_bytes = self.pdf_service.generate_pdf(
            title=report.markdown_content.split("\n")[0].lstrip("# ").strip()
            or project.topic,
            markdown_content=report.markdown_content,
        )
        return filename, pdf_bytes

    async def _clear_previous_results(
        self,
        db: AsyncSession,
        research_id: UUID,
    ) -> None:
        await db.execute(delete(FinalReport).where(FinalReport.research_id == research_id))
        await db.execute(delete(ResearchQuestion).where(ResearchQuestion.research_id == research_id))
        await db.flush()

    async def _persist_workflow_results(
        self,
        db: AsyncSession,
        project: ResearchProject,
        state: dict,
    ) -> None:
        question_map: dict[str, ResearchQuestion] = {}

        for question_data in state.get("questions", []):
            question = ResearchQuestion(
                research_id=project.id,
                question=question_data["question"],
                priority=int(question_data.get("priority", 1)),
            )
            db.add(question)
            await db.flush()
            question_map[question_data["question"]] = question

        source_map: dict[str, SourceResult] = {}

        for source_data in state.get("evaluated_sources", []):
            question_text = source_data.get("question", "")
            question = question_map.get(question_text)

            source = SourceResult(
                research_id=project.id,
                question_id=question.id if question else None,
                title=source_data.get("title", "Untitled"),
                url=source_data.get("url", ""),
                snippet=source_data.get("snippet", ""),
                credibility_score=float(source_data.get("credibility_score", 0)),
                source_type=source_data.get("source_type"),
                published_date=source_data.get("published_date"),
                raw_metadata={"evaluation_notes": source_data.get("evaluation_notes")},
            )
            db.add(source)
            await db.flush()
            source_map[source_data.get("url", "")] = source

        summaries = state.get("summaries", [])
        for summary_data in summaries:
            source = source_map.get(summary_data.get("source_url", ""))
            if source is None:
                continue

            summary = SourceSummary(
                source_id=source.id,
                summary=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points"),
                limitations=summary_data.get("limitations"),
                useful_quotes=summary_data.get("useful_quotes"),
            )
            db.add(summary)

        report_data = state.get("report", {})
        analysis = state.get("analysis", {})
        critique = state.get("critique", {})

        final_report = FinalReport(
            research_id=project.id,
            executive_summary=report_data.get("executive_summary", ""),
            detailed_analysis=report_data.get("detailed_analysis", ""),
            key_findings=report_data.get("key_findings"),
            risks=report_data.get("risks_and_limitations"),
            conclusion=report_data.get("conclusion", ""),
            markdown_content=report_data.get("markdown_content", ""),
            critique_data=critique,
            analysis_data=analysis,
        )
        db.add(final_report)
        await db.flush()
