import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SearchProviderError(Exception):
    """Raised when a search provider fails and fallback is disabled."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider} search failed: {message}")


class SearchProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockSearchProvider(SearchProvider):
    name = "mock"

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        slug = re.sub(r"[^\w]+", "-", query.lower()).strip("-")[:40]
        return [
            {
                "title": f"Overview: {query}",
                "url": f"https://example.com/research/{slug or 'topic'}",
                "snippet": (
                    f"Mock search result for '{query}'. "
                    "Configure Tavily with SEARCH_PROVIDER=tavily for live data."
                ),
                "published_date": "2026-01-15",
                "source_type": "news",
                "raw_metadata": {"provider": "mock"},
            },
            {
                "title": f"Analysis report on {query}",
                "url": f"https://research.example.org/{slug or 'topic'}-analysis",
                "snippet": (
                    f"In-depth analysis covering key drivers, risks, and outlook for {query}."
                ),
                "published_date": "2026-02-01",
                "source_type": "analysis",
                "raw_metadata": {"provider": "mock"},
            },
        ][:max_results]


class TavilySearchProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise SearchProviderError("tavily", "TAVILY_API_KEY is not configured")
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                    "search_depth": "basic",
                },
            )
            if response.status_code == 401:
                raise SearchProviderError("tavily", "Invalid API key (401 Unauthorized)")
            response.raise_for_status()
            data = response.json()

        results: list[dict[str, Any]] = []
        for item in data.get("results", []):
            results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", item.get("snippet", "")),
                    "published_date": item.get("published_date"),
                    "source_type": item.get("source", "web"),
                    "raw_metadata": {
                        "provider": "tavily",
                        "score": item.get("score"),
                        "raw": item,
                    },
                }
            )
        logger.info("Tavily returned %d results for query: %s", len(results), query[:80])
        return results


class SerpAPISearchProvider(SearchProvider):
    name = "serpapi"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise SearchProviderError("serpapi", "SERPAPI_API_KEY is not configured")
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": self.api_key,
                    "engine": "google",
                    "q": query,
                    "num": max_results,
                },
            )
            response.raise_for_status()
            data = response.json()

        results: list[dict[str, Any]] = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "published_date": item.get("date"),
                    "source_type": "web",
                    "raw_metadata": {"provider": "serpapi", "raw": item},
                }
            )
        return results


class SearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.primary_provider = self._build_primary_provider()
        self.fallback_provider = MockSearchProvider()

    def _build_primary_provider(self) -> SearchProvider:
        provider = self.settings.search_provider
        if provider == "tavily":
            return TavilySearchProvider(self.settings.tavily_api_key)
        if provider == "serpapi":
            return SerpAPISearchProvider(self.settings.serpapi_api_key)
        return MockSearchProvider()

    def _max_results(self, max_results: int | None) -> int:
        if max_results is not None:
            return max_results
        if self.settings.search_provider == "tavily":
            return self.settings.tavily_max_results
        return self.settings.max_search_results

    async def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        limit = self._max_results(max_results)
        provider_name = self.primary_provider.name

        try:
            results = await self.primary_provider.search(query, max_results=limit)
            if not results and provider_name != "mock":
                logger.warning("%s returned zero results for: %s", provider_name, query)
            return results
        except Exception as exc:
            logger.error(
                "Search provider '%s' failed for query '%s': %s",
                provider_name,
                query[:80],
                exc,
                exc_info=True,
            )
            if self.settings.allow_search_fallback and provider_name != "mock":
                logger.warning("Falling back to mock search for query: %s", query[:80])
                return await self.fallback_provider.search(query, max_results=limit)
            if isinstance(exc, SearchProviderError):
                raise
            raise SearchProviderError(provider_name, str(exc)) from exc
