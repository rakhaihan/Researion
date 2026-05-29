from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualityStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class CitationValidationResult(BaseModel):
    is_valid: bool
    invalid_citations: list[str] = Field(default_factory=list)
    missing_citation_warnings: list[str] = Field(default_factory=list)
    source_coverage_score: float = Field(ge=0, le=100)
    single_source_dependency_warning: bool = False
    recommendations: list[str] = Field(default_factory=list)


class ClaimCheckResult(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    uncited_high_risk_claims: list[str] = Field(default_factory=list)


class ResearchQualityEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    citation_score: float
    source_diversity_score: float
    source_credibility_score: float
    freshness_score: float
    completeness_score: float
    overall_score: float
    quality_status: QualityStatus
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    citation_validation: CitationValidationResult | None = None
    claim_check: ClaimCheckResult | None = None
    created_at: datetime
