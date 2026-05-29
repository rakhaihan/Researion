from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.agents.critique_agent import CritiqueAgent
from app.agents.report_writer_agent import ReportWriterAgent
from app.db.models import (
    FinalReport,
    QualityStatus,
    ResearchDepth,
    ResearchJob,
    ResearchProject,
    ResearchQualityEvaluation,
    ResearchQuestion,
    ResearchStatus,
    ResearchType,
    SourceResult,
    SourceSummary,
)
from app.schemas.quality import ResearchQualityEvaluationResponse
from app.schemas.research import (
    FinalReportBriefResponse,
    ResearchCreate,
    ResearchDetailResponse,
    ResearchQuestionResponse,
    ResearchSummaryResponse,
    SourceResultResponse,
    SourceSummaryResponse,
)
from app.services.job_service import JobService
from app.services.pdf_service import PDFService
from app.services.quality_evaluation_service import QualityEvaluationService
from app.utils.validators import sanitize_filename, validate_topic
from app.workflows.research_graph import ResearchWorkflow

logger = get_logger(__name__)

ProgressHandler = Callable[[str, int], Awaitable[None]]


class ResearchService:
    def __init__(self) -> None:
        self._workflow: ResearchWorkflow | None = None
        self.pdf_service = PDFService()
        self.job_service = JobService()
        self.quality_service = QualityEvaluationService()
        self.report_writer = ReportWriterAgent()
        self.critique_agent = CritiqueAgent()

    @property
    def workflow(self) -> ResearchWorkflow:
        if self._workflow is None:
            self._workflow = ResearchWorkflow()
        return self._workflow

    async def create_research(
        self,
        db: AsyncSession,
        payload: ResearchCreate,
        user_id: UUID,
    ) -> ResearchProject:
        topic = validate_topic(payload.topic)

        project = ResearchProject(
            user_id=user_id,
            topic=topic,
            research_type=ResearchType(payload.research_type.value),
            depth=ResearchDepth(payload.depth.value),
            status=ResearchStatus.PENDING,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    async def list_research(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[ResearchProject]:
        result = await db.execute(
            select(ResearchProject)
            .where(ResearchProject.user_id == user_id)
            .order_by(ResearchProject.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_research(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID | None = None,
    ) -> ResearchProject:
        query = (
            select(ResearchProject)
            .where(ResearchProject.id == research_id)
            .options(
                selectinload(ResearchProject.questions),
                selectinload(ResearchProject.sources).selectinload(SourceResult.summary),
                selectinload(ResearchProject.final_report),
                selectinload(ResearchProject.quality_evaluation),
            )
        )
        if user_id is not None:
            query = query.where(ResearchProject.user_id == user_id)

        result = await db.execute(query)
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research project not found",
            )
        return project

    def to_detail_response(self, project: ResearchProject) -> ResearchDetailResponse:
        summaries = [
            source.summary
            for source in project.sources
            if source.summary is not None
        ]
        low_credibility_warning = any(
            source.credibility_score is not None and source.credibility_score < 5
            for source in project.sources
        )
        final_report = (
            FinalReportBriefResponse.model_validate(project.final_report)
            if project.final_report
            else None
        )
        quality_eval = None
        warnings: list[str] = []
        recommendations: list[str] = []
        if project.quality_evaluation:
            quality_eval = QualityEvaluationService.to_response(project.quality_evaluation)
            warnings = quality_eval.warnings
            recommendations = quality_eval.recommendations

        return ResearchDetailResponse(
            id=project.id,
            topic=project.topic,
            research_type=project.research_type,
            depth=project.depth,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            questions=[
                ResearchQuestionResponse.model_validate(question)
                for question in project.questions
            ],
            sources=[
                SourceResultResponse.model_validate(source) for source in project.sources
            ],
            summaries=[SourceSummaryResponse.model_validate(summary) for summary in summaries],
            final_report=final_report,
            error_message=project.error_message,
            low_credibility_warning=low_credibility_warning,
            source_count=len(project.sources),
            has_report=final_report is not None,
            quality_status=project.quality_status,
            quality_score=project.quality_score,
            quality_evaluation=quality_eval,
            warnings=warnings,
            recommendations=recommendations,
        )

    async def enqueue_research_run(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> tuple[ResearchProject, ResearchJob]:
        project = await self.get_research(db, research_id, user_id=user_id)
        job = await self.job_service.enqueue_research_job(db, project)
        await db.refresh(project)
        return project, job

    async def execute_research_workflow(
        self,
        db: AsyncSession,
        research_id: UUID,
        on_progress: ProgressHandler | None = None,
    ) -> ResearchProject:
        project = await self.get_research(db, research_id, user_id=None)
        await self._clear_previous_results(db, project.id)

        state = await self.workflow.run(
            topic=project.topic,
            research_type=project.research_type.value,
            depth=project.depth.value,
            on_progress=on_progress,
        )

        await self._persist_workflow_results(db, project, state)
        await self._run_quality_evaluation(db, project.id)
        await db.refresh(project)
        return project

    async def regenerate_report(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> ResearchProject:
        project = await self.get_research(db, research_id, user_id=user_id)
        if not project.sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No sources available. Run full research workflow first.",
            )

        sources = self._sources_to_dict(project.sources)
        summaries = self._summaries_to_dict(project.sources)
        questions = [{"question": q.question, "priority": q.priority} for q in project.questions]

        analysis = (project.final_report.analysis_data if project.final_report else None) or {}
        critique = await self.critique_agent.run(
            analysis=analysis,
            topic=project.topic,
            sources=sources,
            summaries=summaries,
        )

        report_data = await self.report_writer.run(
            topic=project.topic,
            research_type=project.research_type.value,
            questions=questions,
            summaries=summaries,
            analysis=analysis,
            critique=critique,
            sources=sources,
        )

        if project.final_report:
            project.final_report.executive_summary = report_data.get("executive_summary", "")
            project.final_report.detailed_analysis = report_data.get("detailed_analysis", "")
            project.final_report.key_findings = report_data.get("key_findings")
            project.final_report.risks = report_data.get("risks_and_limitations")
            project.final_report.conclusion = report_data.get("conclusion", "")
            project.final_report.markdown_content = report_data.get("markdown_content", "")
            project.final_report.critique_data = critique
            analysis_payload = dict(analysis)
            analysis_payload["report_sources"] = report_data.get("sources", [])
            project.final_report.analysis_data = analysis_payload
        else:
            final_report = FinalReport(
                research_id=project.id,
                executive_summary=report_data.get("executive_summary", ""),
                detailed_analysis=report_data.get("detailed_analysis", ""),
                key_findings=report_data.get("key_findings"),
                risks=report_data.get("risks_and_limitations"),
                conclusion=report_data.get("conclusion", ""),
                markdown_content=report_data.get("markdown_content", ""),
                critique_data=critique,
                analysis_data={
                    **analysis,
                    "report_sources": report_data.get("sources", []),
                },
            )
            db.add(final_report)

        project.status = ResearchStatus.COMPLETED
        await db.flush()
        await self._run_quality_evaluation(db, project.id)
        await db.refresh(project)
        return project

    async def get_quality_evaluation(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> ResearchQualityEvaluationResponse:
        project = await self.get_research(db, research_id, user_id=user_id)
        if project.quality_evaluation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality evaluation not found. Run or regenerate the report first.",
            )
        return QualityEvaluationService.to_response(project.quality_evaluation)

    async def get_report(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> FinalReport:
        project = await self.get_research(db, research_id, user_id=user_id)
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
        user_id: UUID,
    ) -> tuple[str, str]:
        report = await self.get_report(db, research_id, user_id=user_id)
        project = await self.get_research(db, research_id, user_id=user_id)
        filename = f"{sanitize_filename(project.topic)}.md"
        return filename, report.markdown_content

    async def export_pdf(
        self,
        db: AsyncSession,
        research_id: UUID,
        user_id: UUID,
    ) -> tuple[str, bytes]:
        project = await self.get_research(db, research_id, user_id=user_id)
        report = await self.get_report(db, research_id, user_id=user_id)
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
        await db.execute(
            delete(ResearchQualityEvaluation).where(
                ResearchQualityEvaluation.research_id == research_id
            )
        )
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
            accessed_at = self._parse_accessed_at(source_data.get("accessed_at"))

            metadata = source_data.get("raw_metadata") or {}
            if source_data.get("evaluation_notes"):
                metadata = {**metadata, "evaluation_notes": source_data.get("evaluation_notes")}

            source = SourceResult(
                research_id=project.id,
                question_id=question.id if question else None,
                citation_key=source_data.get("citation_key"),
                title=source_data.get("title", "Untitled"),
                url=source_data.get("url", ""),
                snippet=source_data.get("snippet", ""),
                credibility_score=float(source_data.get("credibility_score", 0)),
                credibility_reason=source_data.get("credibility_reason"),
                source_type=source_data.get("source_type"),
                published_date=source_data.get("published_date"),
                raw_metadata=metadata,
                accessed_at=accessed_at,
            )
            db.add(source)
            await db.flush()
            if source_data.get("citation_key"):
                source_map[source_data["citation_key"]] = source
            source_map[source_data.get("url", "")] = source

        summaries = state.get("summaries", [])
        for summary_data in summaries:
            source = source_map.get(summary_data.get("citation_key")) or source_map.get(
                summary_data.get("source_url", "")
            )
            if source is None:
                continue

            summary = SourceSummary(
                source_id=source.id,
                citation_key=summary_data.get("citation_key", source.citation_key),
                summary=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points"),
                limitations=summary_data.get("limitations"),
                useful_quotes=summary_data.get("useful_quotes"),
            )
            db.add(summary)

        report_data = state.get("report", {})
        analysis = state.get("analysis", {})
        critique = state.get("critique", {})

        analysis_payload = dict(analysis)
        analysis_payload["report_sources"] = report_data.get("sources", [])

        final_report = FinalReport(
            research_id=project.id,
            executive_summary=report_data.get("executive_summary", ""),
            detailed_analysis=report_data.get("detailed_analysis", ""),
            key_findings=report_data.get("key_findings"),
            risks=report_data.get("risks_and_limitations"),
            conclusion=report_data.get("conclusion", ""),
            markdown_content=report_data.get("markdown_content", ""),
            critique_data=critique,
            analysis_data=analysis_payload,
        )
        db.add(final_report)
        project.status = ResearchStatus.COMPLETED
        await db.flush()

    async def _run_quality_evaluation(self, db: AsyncSession, research_id: UUID) -> None:
        project = await self.get_research(db, research_id, user_id=None)
        if project.final_report is None:
            return

        scores = self.quality_service.evaluate(project.final_report, list(project.sources))
        await self.quality_service.save_evaluation(db, research_id, scores)
        await self.quality_service.apply_to_project(db, project, scores)

    @staticmethod
    def _sources_to_dict(sources: list[SourceResult]) -> list[dict]:
        return [
            {
                "citation_key": s.citation_key,
                "title": s.title,
                "url": s.url,
                "snippet": s.snippet,
                "credibility_score": s.credibility_score,
                "credibility_reason": s.credibility_reason,
                "source_type": s.source_type,
                "published_date": s.published_date,
                "question": "",
            }
            for s in sources
        ]

    @staticmethod
    def _summaries_to_dict(sources: list[SourceResult]) -> list[dict]:
        summaries: list[dict] = []
        for source in sources:
            if source.summary is None:
                continue
            summaries.append(
                {
                    "citation_key": source.summary.citation_key or source.citation_key,
                    "source_url": source.url,
                    "source_title": source.title,
                    "summary": source.summary.summary,
                    "key_points": source.summary.key_points,
                    "limitations": source.summary.limitations,
                }
            )
        return summaries

    @staticmethod
    def _parse_accessed_at(value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
