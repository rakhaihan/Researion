from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResearchType(str, Enum):
    MARKET_RESEARCH = "Market Research"
    STOCK_CRYPTO = "Stock/Crypto Research"
    ACADEMIC = "Academic Research"
    COMPETITOR = "Competitor Analysis"
    TECHNOLOGY_TREND = "Technology Trend Analysis"


class ResearchDepth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING = "evaluating"
    SUMMARIZING = "summarizing"
    ANALYZING = "analyzing"
    CRITIQUING = "critiquing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    research_type: ResearchType
    depth: ResearchDepth = ResearchDepth.STANDARD


class ResearchQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    priority: int


class SourceResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_id: UUID | None
    title: str
    url: str
    snippet: str
    credibility_score: float | None
    source_type: str | None
    published_date: str | None


class SourceSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    summary: str
    key_points: list[str] | None
    limitations: str | None


class ResearchSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic: str
    research_type: ResearchType
    depth: ResearchDepth
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime


class ResearchDetailResponse(ResearchSummaryResponse):
    questions: list[ResearchQuestionResponse] = Field(default_factory=list)
    sources: list[SourceResultResponse] = Field(default_factory=list)
    error_message: str | None = None
