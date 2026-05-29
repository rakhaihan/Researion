import mimetypes
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.redis import get_arq_pool
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.schemas.documents import DocumentDetailResponse, DocumentResponse, DocumentStatusResponse
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_storage_service import DocumentStorageService
from app.services.embedding_service import EmbeddingService

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
ALLOWED_MIME = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
}


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = DocumentStorageService()
        self.processor = DocumentProcessingService()
        self.embedding_service = EmbeddingService()

    async def upload_document(
        self,
        db: AsyncSession,
        user_id: UUID,
        file: UploadFile,
    ) -> DocumentResponse:
        if not file.filename:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Filename is required")

        safe_name = self.storage.sanitize_filename(file.filename)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        guessed_type = mimetypes.guess_type(safe_name)[0]
        content_type = file.content_type or guessed_type or "application/octet-stream"
        if content_type not in ALLOWED_MIME and suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported MIME type")

        data = await file.read()
        if len(data) > self.settings.max_document_size_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {self.settings.max_document_size_mb}MB limit",
            )
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Empty file")

        document = Document(
            user_id=user_id,
            filename=safe_name,
            original_filename=file.filename,
            content_type=content_type,
            file_size=len(data),
            storage_path="",
            status=DocumentStatus.UPLOADED,
        )
        db.add(document)
        await db.flush()

        storage_path = self.storage.build_storage_path(user_id, document.id, safe_name)
        storage_path.write_bytes(data)
        document.storage_path = str(storage_path)
        await db.flush()

        await self._enqueue_processing(document.id)
        await db.refresh(document)
        return self._to_response(document, chunk_count=0)

    async def list_documents(self, db: AsyncSession, user_id: UUID) -> list[DocumentResponse]:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        documents = list(result.scalars().all())
        responses: list[DocumentResponse] = []
        for doc in documents:
            count = await self._chunk_count(db, doc.id)
            responses.append(self._to_response(doc, chunk_count=count))
        return responses

    async def get_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
    ) -> DocumentDetailResponse:
        document = await self._get_owned(db, document_id, user_id)
        count = await self._chunk_count(db, document.id)
        base = self._to_response(document, chunk_count=count)
        return DocumentDetailResponse(
            **base.model_dump(),
            processing_step=document.processing_step,
        )

    async def get_status(
        self,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
    ) -> DocumentStatusResponse:
        document = await self._get_owned(db, document_id, user_id)
        count = await self._chunk_count(db, document.id)
        return DocumentStatusResponse(
            id=document.id,
            status=document.status,
            processing_step=document.processing_step,
            error_message=document.error_message,
            chunk_count=count,
        )

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
    ) -> None:
        document = await self._get_owned(db, document_id, user_id)
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        await db.delete(document)
        await db.flush()
        self.storage.delete_document_files(user_id, document_id)

    async def validate_documents_for_research(
        self,
        db: AsyncSession,
        user_id: UUID,
        document_ids: list[UUID],
    ) -> None:
        if not document_ids:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="At least one processed document is required for this source mode",
            )
        result = await db.execute(
            select(Document).where(
                Document.id.in_(document_ids),
                Document.user_id == user_id,
            )
        )
        docs = {doc.id: doc for doc in result.scalars().all()}
        missing = [str(doc_id) for doc_id in document_ids if doc_id not in docs]
        if missing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Documents not found or not owned by user: {', '.join(missing)}",
            )
        not_processed = [
            str(doc.id)
            for doc in docs.values()
            if doc.status != DocumentStatus.PROCESSED
        ]
        if not_processed:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Documents must be processed before use in research: "
                    f"{', '.join(not_processed)}"
                ),
            )

    async def process_document(self, db: AsyncSession, document_id: UUID) -> None:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            return

        try:
            document.status = DocumentStatus.PROCESSING
            document.processing_step = "extracting"
            document.error_message = None
            await db.flush()

            file_path = Path(document.storage_path)
            pages = self.processor.extract_text(file_path, document.content_type)

            document.processing_step = "chunking"
            await db.flush()

            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
            chunk_specs = self.processor.chunk_pages(pages)

            document.processing_step = "embedding"
            await db.flush()

            texts = [spec["content"] for spec in chunk_specs]
            embeddings = await self.embedding_service.embed_texts(texts)

            for spec, embedding in zip(chunk_specs, embeddings, strict=False):
                chunk = DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=spec["chunk_index"],
                    content=spec["content"],
                    token_count=spec["token_count"],
                    page_number=spec.get("page_number"),
                    section_title=spec.get("section_title"),
                    embedding=embedding,
                    embedding_id=f"{document.id}:{spec['chunk_index']}",
                )
                db.add(chunk)

            document.status = DocumentStatus.PROCESSED
            document.processing_step = "processed"
            await db.flush()
            logger.info("Document %s processed with %s chunks", document.id, len(chunk_specs))
        except Exception as exc:
            logger.exception("Document processing failed for %s", document_id)
            document.status = DocumentStatus.FAILED
            document.processing_step = "failed"
            document.error_message = str(exc)[:2000]
            await db.flush()
            raise

    async def _enqueue_processing(self, document_id: UUID) -> None:
        pool = await get_arq_pool()
        await pool.enqueue_job("process_document_job", str(document_id))

    async def _get_owned(
        self,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
    ) -> Document:
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    async def _chunk_count(self, db: AsyncSession, document_id: UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(DocumentChunk).where(
                DocumentChunk.document_id == document_id
            )
        )
        return int(result.scalar_one())

    @staticmethod
    def _to_response(document: Document, chunk_count: int) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            content_type=document.content_type,
            file_size=document.file_size,
            status=document.status,
            error_message=document.error_message,
            chunk_count=chunk_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
