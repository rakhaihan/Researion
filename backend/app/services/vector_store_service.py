from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk
from app.services.embedding_service import EmbeddingService


class VectorStoreService:
    """JSONB embedding storage with in-app cosine similarity (pgvector-ready abstraction)."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        db: AsyncSession,
        user_id: UUID,
        query_embedding: list[float],
        *,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        stmt = select(DocumentChunk).where(
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.isnot(None),
        )
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        result = await db.execute(stmt)
        chunks = list(result.scalars().all())

        scored: list[tuple[DocumentChunk, float]] = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            score = self.embedding_service.cosine_similarity(query_embedding, chunk.embedding)
            scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
