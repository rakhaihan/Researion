from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentAnchorType(StrEnum):
    REPORT = "report"
    SOURCE = "source"
    GENERAL = "general"


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: UUID | None = None
    anchor_type: CommentAnchorType | None = None
    anchor_ref: str | None = Field(default=None, max_length=200)


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    research_id: UUID
    user_id: UUID
    parent_id: UUID | None
    content: str
    anchor_type: str | None
    anchor_ref: str | None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime
    replies: list["CommentResponse"] = Field(default_factory=list)


CommentResponse.model_rebuild()
