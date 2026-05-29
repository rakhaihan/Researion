from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.agents.base import BaseAgent
from app.services.rag_service import RAGService
from app.services.search_service import SearchService
from app.utils.citations import assign_citation_keys
from app.utils.url_utils import normalize_url


class SearchAgent(BaseAgent):
    name = "search_agent"

    def __init__(
        self,
        llm_service=None,
        search_service: SearchService | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        super().__init__(llm_service)
        self.search_service = search_service or SearchService()
        self.rag_service = rag_service or RAGService()

    async def run(
        self,
        questions: list[dict[str, Any]],
        topic: str,
        *,
        research_source_mode: str = "web_only",
        document_ids: list[str] | None = None,
        user_id: UUID | None = None,
        db=None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        all_sources: list[dict[str, Any]] = []
        accessed_at = datetime.now(UTC).isoformat()

        if research_source_mode in {"documents_only", "hybrid"}:
            if db is None or user_id is None:
                raise ValueError("db and user_id required for document retrieval")
            doc_uuids = [UUID(doc_id) for doc_id in (document_ids or [])]
            all_sources.extend(
                await self._fetch_document_sources(
                    db, user_id, doc_uuids, questions, topic, accessed_at
                )
            )

        if research_source_mode in {"web_only", "hybrid"}:
            all_sources.extend(
                await self._fetch_web_sources(questions, topic, accessed_at)
            )

        return assign_citation_keys(all_sources)

    async def _fetch_web_sources(
        self,
        questions: list[dict[str, Any]],
        topic: str,
        accessed_at: str,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for question_item in questions:
            question = question_item["question"]
            query = f"{topic} {question}"
            search_results = await self.search_service.search(query)

            for result in search_results:
                url = result.get("url", "")
                if not url:
                    continue
                normalized = normalize_url(url)
                if normalized in seen_urls:
                    continue
                seen_urls.add(normalized)

                results.append(
                    {
                        "question": question,
                        "question_priority": question_item.get("priority", 1),
                        "title": result.get("title", "Untitled"),
                        "url": url,
                        "snippet": result.get("snippet", ""),
                        "published_date": result.get("published_date"),
                        "source_type": "web",
                        "raw_metadata": result.get("raw_metadata"),
                        "accessed_at": accessed_at,
                        "normalized_url": normalized,
                    }
                )
        return results

    async def _fetch_document_sources(
        self,
        db,
        user_id: UUID,
        document_ids: list[UUID],
        questions: list[dict[str, Any]],
        topic: str,
        accessed_at: str,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_chunks: set[str] = set()

        for question_item in questions:
            question = question_item["question"]
            query = f"{topic} {question}"
            chunks = await self.rag_service.retrieve_relevant_chunks(
                db,
                user_id,
                query,
                document_ids=document_ids or None,
            )
            for chunk in chunks:
                key = str(chunk.chunk_id)
                if key in seen_chunks:
                    continue
                seen_chunks.add(key)

                page_label = f", page {chunk.page_number}" if chunk.page_number else ""
                title = f"{chunk.filename}{page_label}"
                url = f"document://{chunk.document_id}/chunk/{chunk.chunk_id}"
                excerpt = chunk.content[:500]

                results.append(
                    {
                        "question": question,
                        "question_priority": question_item.get("priority", 1),
                        "title": title,
                        "url": url,
                        "snippet": excerpt,
                        "published_date": None,
                        "source_type": "document",
                        "document_id": str(chunk.document_id),
                        "chunk_id": str(chunk.chunk_id),
                        "page_number": chunk.page_number,
                        "accessed_at": accessed_at,
                        "rag_score": chunk.score,
                        "original_filename": chunk.filename,
                    }
                )
        return results
