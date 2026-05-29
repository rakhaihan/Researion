from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStep(StrEnum):
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING_SOURCES = "evaluating_sources"
    SUMMARIZING = "summarizing"
    ANALYZING = "analyzing"
    CRITIQUING = "critiquing"
    WRITING_REPORT = "writing_report"
    COMPLETED = "completed"


STEP_LABELS: dict[str, str] = {
    ResearchStep.PLANNING.value: "Planning research questions",
    ResearchStep.SEARCHING.value: "Searching sources",
    ResearchStep.EVALUATING_SOURCES.value: "Evaluating source credibility",
    ResearchStep.SUMMARIZING.value: "Summarizing sources",
    ResearchStep.ANALYZING.value: "Performing analysis",
    ResearchStep.CRITIQUING.value: "Critiquing analysis",
    ResearchStep.WRITING_REPORT.value: "Writing final report",
    ResearchStep.COMPLETED.value: "Completed",
}


class ResearchRunResponse(BaseModel):
    research_id: UUID
    job_id: str
    status: JobStatus
    message: str


class ResearchProgressResponse(BaseModel):
    research_id: UUID
    job_id: str | None
    status: JobStatus
    current_step: str | None
    current_step_label: str | None = None
    progress_percentage: int
    error_message: str | None
    started_at: datetime | None = None
    updated_at: datetime


class JobCleanupResponse(BaseModel):
    deleted_count: int
    older_than_days: int


class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    job_id: str | None
    current_step: str | None
    status: JobStatus
    progress_percentage: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
