import pytest

from app.schemas.agent_outputs import AnalystOutput, PlannerOutput, ResearchQuestionPlan, ReportWriterOutput
from app.services.citation_validation_service import CitationValidationService
from app.services.claim_checker_service import ClaimCheckerService
from app.services.llm_service import LLMService
from app.services.quality_evaluation_service import QualityEvaluationService
from app.schemas.quality import QualityStatus
from app.db.models import FinalReport, SourceResult
from uuid import uuid4


def test_planner_output_schema():
    output = PlannerOutput(
        questions=[
            ResearchQuestionPlan(
                question="What drives EV adoption in 2026?",
                priority=1,
                rationale="Core market driver.",
            )
        ]
    )
    assert len(output.questions) == 1


def test_analyst_output_confidence_enum():
    output = AnalystOutput(
        analysis="Market grows [S1].",
        confidence_level="high",
    )
    assert output.confidence_level == "high"


def test_llm_parse_json_extracts_object():
    raw = 'Here is data {"analysis": "test", "patterns": [], "supporting_evidence": [], "opportunities": [], "risks": [], "conflicting_signals": [], "confidence_level": "low"}'
    parsed = LLMService._parse_json(raw, {})
    assert parsed.get("analysis") == "test"


@pytest.mark.asyncio
async def test_llm_structured_fallback_on_invalid():
    llm = LLMService()
    fallback = AnalystOutput(
        analysis="fallback",
        confidence_level="low",
    )

    async def fake_invoke(system_prompt, user_prompt):
        return "not json at all"

    llm._invoke_llm = fake_invoke  # type: ignore[method-assign]

    result, warnings = await llm.generate_structured(
        "system",
        "user",
        AnalystOutput,
        fallback,
        max_retries=1,
    )
    assert result.analysis == "fallback"
    assert warnings


def test_citation_validation_detects_fictitious():
    service = CitationValidationService()
    result = service.validate(
        markdown_content="Growth is strong [S1][S99].",
        key_findings=["Revenue up 20% [S1]"],
        conclusion="Outlook positive [S2]",
        valid_citation_keys={"S1", "S2"},
        report_sources=[{"citation_key": "S1"}, {"citation_key": "S2"}],
    )
    assert "S99" in result.invalid_citations
    assert result.is_valid is False


def test_claim_checker_flags_numeric_without_citation():
    service = ClaimCheckerService()
    result = service.check(
        key_findings=["Revenue increased 25% year over year"],
    )
    assert result.uncited_high_risk_claims
    assert result.warnings


def test_quality_gate_status_thresholds():
    service = QualityEvaluationService()
    from app.schemas.quality import CitationValidationResult

    citation = CitationValidationResult(
        is_valid=True,
        source_coverage_score=90,
    )
    assert service._quality_status(85, citation) == QualityStatus.PASSED
    assert service._quality_status(70, citation) == QualityStatus.WARNING
    assert service._quality_status(50, citation) == QualityStatus.FAILED


def test_quality_evaluation_scores():
    service = QualityEvaluationService()
    report = FinalReport(
        id=uuid4(),
        research_id=uuid4(),
        executive_summary="Summary",
        detailed_analysis="## Detailed Analysis\nContent [S1]",
        key_findings=["Finding [S1]"],
        conclusion="Done [S1]",
        markdown_content=(
            "# Report\n\n## Executive Summary\n\n## Key Findings\n\n"
            "## Detailed Analysis\n\n## Conclusion\n\n## Sources\n"
        ),
    )
    sources = [
        SourceResult(
            id=uuid4(),
            research_id=report.research_id,
            citation_key="S1",
            title="Source 1",
            url="https://example.com/1",
            snippet="text",
            credibility_score=8.0,
        ),
        SourceResult(
            id=uuid4(),
            research_id=report.research_id,
            citation_key="S2",
            title="Source 2",
            url="https://other.com/2",
            snippet="text",
            credibility_score=7.0,
        ),
    ]
    scores = service.evaluate(report, sources)
    assert 0 <= scores["overall_score"] <= 100
    assert scores["quality_status"] in QualityStatus
