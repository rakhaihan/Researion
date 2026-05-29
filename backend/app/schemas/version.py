from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.quality import QualityStatus


class ReportVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    version_number: int
    executive_summary: str
    detailed_analysis: str
    key_findings: list | None
    risks: list | None
    conclusion: str
    markdown_content: str
    quality_score: float | None
    quality_status: QualityStatus | None
    created_by: UUID | None
    change_reason: str | None
    created_at: datetime


class VersionCompareResponse(BaseModel):
    from_version: int
    to_version: int
    added_sections: list[str]
    removed_sections: list[str]
    changed_summary: str
    markdown_diff: str
