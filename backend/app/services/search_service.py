import re
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import Settings, get_settings


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockSearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        slug = re.sub(r"[^\w]+", "-", query.lower()).strip("-")[:40]
        return [
            {
                "title": f"Overview: {query}",
                "url": f"https://example.com/research/{slug or 'topic'}",
                "snippet": f"Mock search result for '{query}'. Configure Tavily or SerpAPI for live data.",
                "published_date": "2026-01-15",
                "source_type": "news",
            },
            {
                "title": f"Analysis report on {query}",
                "url": f"https://research.example.org/{slug or 'topic'}-analysis",
                "snippet": f"In-depth analysis covering key drivers, risks, and market outlook for {query}.",
                "published_date": "2026-02-01",
                "source_type": "analysis",
            },
        ][:max_results]


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
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
                }
            )
        return results


class SerpAPISearchProvider(SearchProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        import httpx

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
                }
            )
        return results


class SearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = self._build_provider()

    def _build_provider(self) -> SearchProvider:
        provider = self.settings.search_provider
        if provider == "tavily" and self.settings.tavily_api_key:
            return TavilySearchProvider(self.settings.tavily_api_key)
        if provider == "serpapi" and self.settings.serpapi_api_key:
            return SerpAPISearchProvider(self.settings.serpapi_api_key)
        return MockSearchProvider()

    async def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        limit = max_results or self.settings.max_search_results
        return await self.provider.search(query, max_results=limit)
