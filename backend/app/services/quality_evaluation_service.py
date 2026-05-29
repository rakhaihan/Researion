from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    FinalReport,
    ResearchProject,
    ResearchQualityEvaluation,
    SourceResult,
)
from app.db.models import (
    QualityStatus as DbQualityStatus,
)
from app.schemas.quality import (
    CitationValidationResult,
    ClaimCheckResult,
    QualityStatus,
    ResearchQualityEvaluationResponse,
)
from app.services.citation_validation_service import CitationValidationService
from app.services.claim_checker_service import ClaimCheckerService

REQUIRED_SECTIONS = [
    "executive summary",
    "key findings",
    "detailed analysis",
    "conclusion",
    "sources",
]


class QualityEvaluationService:
    def __init__(self) -> None:
        self.citation_validator = CitationValidationService()
        self.claim_checker = ClaimCheckerService()

    def evaluate(
        self,
        report: FinalReport,
        sources: list[SourceResult],
        *,
        citation_validation: CitationValidationResult | None = None,
        claim_check: ClaimCheckResult | None = None,
    ) -> dict:
        valid_keys = {s.citation_key for s in sources if s.citation_key}
        report_sources = (report.analysis_data or {}).get("report_sources")
        if not report_sources and report.key_findings:
            report_sources = []

        citation_result = citation_validation or self.citation_validator.validate(
            markdown_content=report.markdown_content,
            key_findings=report.key_findings or [],
            conclusion=report.conclusion,
            valid_citation_keys=valid_keys,
            report_sources=report_sources,
        )
        claim_result = claim_check or self.claim_checker.check(
            key_findings=report.key_findings or [],
            markdown_content=report.markdown_content,
        )

        citation_score = self._citation_score(citation_result)
        diversity_score = self._diversity_score(sources)
        credibility_score = self._credibility_score(sources)
        freshness_score = self._freshness_score(sources)
        completeness_score = self._completeness_score(report)

        overall = round(
            citation_score * 0.3
            + diversity_score * 0.15
            + credibility_score * 0.2
            + freshness_score * 0.15
            + completeness_score * 0.2,
            1,
        )

        status = self._quality_status(overall, citation_result)

        warnings = list(citation_result.missing_citation_warnings)
        warnings.extend(claim_result.warnings[:10])
        if citation_result.invalid_citations:
            warnings.insert(0, f"Invalid citations: {', '.join(citation_result.invalid_citations)}")

        recommendations = list(citation_result.recommendations)
        if status == QualityStatus.FAILED:
            recommendations.append("Consider regenerating the report with stricter citation rules.")
        elif status == QualityStatus.WARNING:
            recommendations.append("Review warnings before sharing the report externally.")

        return {
            "citation_score": citation_score,
            "source_diversity_score": diversity_score,
            "source_credibility_score": credibility_score,
            "freshness_score": freshness_score,
            "completeness_score": completeness_score,
            "overall_score": overall,
            "quality_status": status,
            "warnings": warnings,
            "recommendations": recommendations,
            "citation_validation": citation_result.model_dump(),
            "claim_check": claim_result.model_dump(),
        }

    async def save_evaluation(
        self,
        db: AsyncSession,
        research_id: UUID,
        scores: dict,
    ) -> ResearchQualityEvaluation:
        existing = await db.execute(
            select(ResearchQualityEvaluation).where(
                ResearchQualityEvaluation.research_id == research_id
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            await db.delete(row)
            await db.flush()

        raw_status = scores["quality_status"]
        status_value = raw_status.value if hasattr(raw_status, "value") else raw_status

        evaluation = ResearchQualityEvaluation(
            research_id=research_id,
            citation_score=scores["citation_score"],
            source_diversity_score=scores["source_diversity_score"],
            source_credibility_score=scores["source_credibility_score"],
            freshness_score=scores["freshness_score"],
            completeness_score=scores["completeness_score"],
            overall_score=scores["overall_score"],
            quality_status=DbQualityStatus(status_value),
            warnings=scores.get("warnings"),
            recommendations=scores.get("recommendations"),
            citation_validation=scores.get("citation_validation"),
            claim_check=scores.get("claim_check"),
        )
        db.add(evaluation)
        await db.flush()
        await db.refresh(evaluation)
        return evaluation

    async def apply_to_project(
        self,
        db: AsyncSession,
        project: ResearchProject,
        scores: dict,
    ) -> None:
        raw_status = scores["quality_status"]
        status_value = raw_status.value if hasattr(raw_status, "value") else raw_status
        project.quality_status = DbQualityStatus(status_value)
        project.quality_score = scores["overall_score"]
        await db.flush()

    @staticmethod
    def _quality_status(overall: float, citation: CitationValidationResult) -> QualityStatus:
        if citation.invalid_citations or overall < 60:
            return QualityStatus.FAILED
        if overall < 80:
            return QualityStatus.WARNING
        return QualityStatus.PASSED

    @staticmethod
    def _citation_score(result: CitationValidationResult) -> float:
        score = result.source_coverage_score
        if result.invalid_citations:
            score = min(score, 40)
        if result.single_source_dependency_warning:
            score = max(0, score - 15)
        return round(min(100, score), 1)

    @staticmethod
    def _diversity_score(sources: list[SourceResult]) -> float:
        if not sources:
            return 0.0
        domains: set[str] = set()
        for source in sources:
            try:
                from app.utils.url_utils import extract_domain

                domains.add(extract_domain(source.url))
            except Exception:
                domains.add(source.url)
        unique = len(domains)
        total = len(sources)
        ratio = unique / total if total else 0
        return round(min(100, 40 + ratio * 60), 1)

    @staticmethod
    def _credibility_score(sources: list[SourceResult]) -> float:
        scores = [s.credibility_score for s in sources if s.credibility_score is not None]
        if not scores:
            return 50.0
        avg = sum(scores) / len(scores)
        return round(min(100, avg * 10), 1)

    @staticmethod
    def _freshness_score(sources: list[SourceResult]) -> float:
        if not sources:
            return 50.0
        dated = sum(1 for s in sources if s.published_date or s.accessed_at)
        ratio = dated / len(sources)
        return round(min(100, 50 + ratio * 50), 1)

    @staticmethod
    def _completeness_score(report: FinalReport) -> float:
        md = (report.markdown_content or "").lower()
        found = sum(1 for section in REQUIRED_SECTIONS if section in md)
        base = (found / len(REQUIRED_SECTIONS)) * 100
        if report.executive_summary and report.conclusion:
            base = min(100, base + 10)
        return round(base, 1)

    @staticmethod
    def to_response(evaluation: ResearchQualityEvaluation) -> ResearchQualityEvaluationResponse:
        from app.schemas.quality import CitationValidationResult, ClaimCheckResult

        citation = None
        if evaluation.citation_validation:
            citation = CitationValidationResult.model_validate(evaluation.citation_validation)
        claim = None
        if evaluation.claim_check:
            claim = ClaimCheckResult.model_validate(evaluation.claim_check)

        return ResearchQualityEvaluationResponse(
            id=evaluation.id,
            research_id=evaluation.research_id,
            citation_score=evaluation.citation_score,
            source_diversity_score=evaluation.source_diversity_score,
            source_credibility_score=evaluation.source_credibility_score,
            freshness_score=evaluation.freshness_score,
            completeness_score=evaluation.completeness_score,
            overall_score=evaluation.overall_score,
            quality_status=evaluation.quality_status,
            warnings=evaluation.warnings or [],
            recommendations=evaluation.recommendations or [],
            citation_validation=citation,
            claim_check=claim,
            created_at=evaluation.created_at,
        )
