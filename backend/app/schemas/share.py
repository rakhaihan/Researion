from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShareVisibility(StrEnum):
    PRIVATE = "private"
    PUBLIC = "public"


class ShareLinkCreate(BaseModel):
    visibility: ShareVisibility = ShareVisibility.PUBLIC
    expires_at: datetime | None = None
    allow_download: bool = False


class ShareLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    token: str
    visibility: ShareVisibility
    expires_at: datetime | None
    allow_download: bool
    created_at: datetime
    revoked_at: datetime | None
    share_url: str | None = None


class PublicSourceResponse(BaseModel):
    citation_key: str | None
    title: str
    source_type: str | None = None
    page_number: int | None = None
    snippet: str | None = None


class PublicReportResponse(BaseModel):
    title: str
    markdown_content: str
    quality_score: float | None
    quality_status: str | None
    sources: list[PublicSourceResponse]
    created_at: datetime
    updated_at: datetime
    allow_download: bool
