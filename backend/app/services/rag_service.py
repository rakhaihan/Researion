from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentStatus
from app.schemas.documents import RAGChunkResult
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


class RAGService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    async def retrieve_relevant_chunks(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ) -> list[RAGChunkResult]:
        query_embedding = await self.embedding_service.embed_text(query)
        matches = await self.vector_store.search(
            db,
            user_id,
            query_embedding,
            document_ids=document_ids,
            top_k=top_k,
        )

        if not matches:
            return []

        doc_ids = {chunk.document_id for chunk, _ in matches}
        doc_result = await db.execute(
            select(Document).where(
                Document.id.in_(doc_ids),
                Document.user_id == user_id,
                Document.status == DocumentStatus.PROCESSED,
            )
        )
        documents = {doc.id: doc for doc in doc_result.scalars().all()}

        results: list[RAGChunkResult] = []
        for chunk, score in matches:
            doc = documents.get(chunk.document_id)
            if doc is None:
                continue
            results.append(
                RAGChunkResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    filename=doc.original_filename,
                    content=chunk.content,
                    score=round(score, 4),
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                )
            )
        return results
