from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ResearchSourceMode(StrEnum):
    WEB_ONLY = "web_only"
    DOCUMENTS_ONLY = "documents_only"
    HYBRID = "hybrid"


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: DocumentStatus
    error_message: str | None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    processing_step: str | None = None


class DocumentStatusResponse(BaseModel):
    id: UUID
    status: DocumentStatus
    processing_step: str | None = None
    error_message: str | None = None
    chunk_count: int = 0


class RAGChunkResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    score: float
    page_number: int | None = None
    section_title: str | None = None
    citation_key_candidate: str | None = None
