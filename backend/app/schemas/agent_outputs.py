from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConfidenceLevel = Literal["low", "medium", "high"]


class ResearchQuestionPlan(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    priority: int = Field(..., ge=1, le=20)
    rationale: str = Field(default="", max_length=1000)


class PlannerOutput(BaseModel):
    questions: list[ResearchQuestionPlan] = Field(..., min_length=1, max_length=12)


class SearchResultItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., min_length=4, max_length=2000)
    snippet: str = Field(default="", max_length=5000)
    question: str = Field(default="")


class SearchAgentOutput(BaseModel):
    results: list[SearchResultItem] = Field(default_factory=list)


class SourceEvaluationItem(BaseModel):
    citation_key: str | None = None
    url: str = ""
    credibility_score: float = Field(..., ge=1.0, le=10.0)
    source_type: str = Field(default="unknown", max_length=100)
    credibility_reason: str = Field(default="", max_length=2000)
    is_primary_source: bool = False
    evaluation_notes: str | None = None


class SourceEvaluationOutput(BaseModel):
    evaluations: list[SourceEvaluationItem] = Field(default_factory=list)


class SourceSummaryItem(BaseModel):
    citation_key: str = Field(..., pattern=r"^S\d+$")
    summary: str = Field(..., min_length=10)
    key_points: list[str] = Field(default_factory=list)
    useful_quotes: list[str] = Field(default_factory=list)
    limitations: str = Field(default="")
    source_url: str | None = None


class SourceSummaryOutput(BaseModel):
    summaries: list[SourceSummaryItem] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    claim: str = Field(..., min_length=3)
    citations: list[str] = Field(default_factory=list)

    @field_validator("citations")
    @classmethod
    def validate_citation_keys(cls, value: list[str]) -> list[str]:
        return [c for c in value if c and c.startswith("S")]


class AnalystOutput(BaseModel):
    analysis: str = Field(default="", min_length=1)
    patterns: list[str] = Field(default_factory=list)
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    conflicting_signals: list[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = "medium"


class CritiqueOutput(BaseModel):
    weaknesses: list[str] = Field(default_factory=list)
    missing_perspectives: list[str] = Field(default_factory=list)
    possible_bias: list[str] = Field(default_factory=list)
    over_reliance_on_single_source: bool = False
    uncited_claims: list[str] = Field(default_factory=list)
    outdated_sources: list[str] = Field(default_factory=list)
    low_credibility_sources: list[str] = Field(default_factory=list)
    missing_perspective_areas: list[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = "medium"


class ReportSourceItem(BaseModel):
    citation_key: str = Field(..., pattern=r"^S\d+$")
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=4)


class ReportWriterOutput(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    executive_summary: str = Field(..., min_length=10)
    key_findings: list[str] = Field(default_factory=list)
    detailed_analysis: str = Field(default="", min_length=1)
    risks_and_limitations: list[str] = Field(default_factory=list)
    opposing_views: list[str] = Field(default_factory=list)
    conclusion: str = Field(default="", min_length=1)
    sources: list[ReportSourceItem] = Field(default_factory=list)
    markdown_content: str = Field(default="")
    research_questions: list[str] = Field(default_factory=list)
    methodology: str = Field(default="")
