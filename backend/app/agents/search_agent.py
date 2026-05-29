from datetime import UTC, datetime
from typing import Any

from app.agents.base import BaseAgent
from app.services.search_service import SearchService
from app.utils.citations import assign_citation_keys
from app.utils.url_utils import normalize_url


class SearchAgent(BaseAgent):
    name = "search_agent"

    def __init__(
        self,
        llm_service=None,
        search_service: SearchService | None = None,
    ) -> None:
        super().__init__(llm_service)
        self.search_service = search_service or SearchService()

    async def run(
        self,
        questions: list[dict[str, Any]],
        topic: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        all_sources: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        accessed_at = datetime.now(UTC).isoformat()

        for question_item in questions:
            question = question_item["question"]
            query = f"{topic} {question}"
            results = await self.search_service.search(query)

            for result in results:
                url = result.get("url", "")
                if not url:
                    continue

                normalized = normalize_url(url)
                if normalized in seen_urls:
                    continue
                seen_urls.add(normalized)

                all_sources.append(
                    {
                        "question": question,
                        "question_priority": question_item.get("priority", 1),
                        "title": result.get("title", "Untitled"),
                        "url": url,
                        "snippet": result.get("snippet", ""),
                        "published_date": result.get("published_date"),
                        "source_type": result.get("source_type", "web"),
                        "raw_metadata": result.get("raw_metadata"),
                        "accessed_at": accessed_at,
                        "normalized_url": normalized,
                    }
                )

        return assign_citation_keys(all_sources)
