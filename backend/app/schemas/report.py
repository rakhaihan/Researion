from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinalReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    executive_summary: str
    detailed_analysis: str
    key_findings: list[str] | None
    risks: list[str] | None
    conclusion: str
    markdown_content: str
    critique_data: dict | None = None
    analysis_data: dict | None = None


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    content: str | None = None
