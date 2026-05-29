from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.services.search_service import (
    SearchProviderError,
    SearchService,
    TavilySearchProvider,
)
from app.utils.citations import assign_citation_keys, build_sources_markdown_section
from app.utils.url_utils import normalize_url


def test_normalize_url_strips_tracking_params():
    url = "https://Example.com/path/?utm_source=x&id=1&utm_medium=email&fbclid=abc"
    normalized = normalize_url(url)
    assert "utm_" not in normalized
    assert "fbclid" not in normalized
    assert "example.com" in normalized
    assert normalized.endswith("id=1") or "id=1" in normalized


def test_normalize_url_removes_trailing_slash():
    assert normalize_url("https://example.com/page/") == normalize_url("https://example.com/page")


def test_url_deduplication_same_normalized_url():
    url_a = "https://www.example.com/article/?utm_source=google"
    url_b = "https://example.com/article"
    assert normalize_url(url_a) == normalize_url(url_b)


def test_assign_citation_keys_consistent():
    sources = [{"title": "A", "url": "https://a.com"}, {"title": "B", "url": "https://b.com"}]
    result = assign_citation_keys(sources)
    assert result[0]["citation_key"] == "S1"
    assert result[1]["citation_key"] == "S2"


def test_build_sources_markdown_section():
    sources = [
        {"citation_key": "S2", "title": "Second", "url": "https://b.com"},
        {"citation_key": "S1", "title": "First", "url": "https://a.com"},
    ]
    lines = build_sources_markdown_section(sources)
    text = "\n".join(lines)
    assert "## Sources" in text
    assert "[S1] First — https://a.com" in text
    assert "[S2] Second — https://b.com" in text
    assert text.index("[S1]") < text.index("[S2]")


@pytest.mark.asyncio
async def test_tavily_provider_called_when_configured():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "title": "NVIDIA Outlook",
                "url": "https://example.com/nvidia",
                "content": "Strong data center demand.",
                "published_date": "2026-01-01",
                "score": 0.9,
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    provider = TavilySearchProvider("test-key")

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await provider.search("NVIDIA stock", max_results=3)

    mock_client.post.assert_awaited_once()
    assert results[0]["title"] == "NVIDIA Outlook"
    assert results[0]["raw_metadata"]["provider"] == "tavily"


@pytest.mark.asyncio
async def test_fallback_to_mock_when_tavily_fails_and_fallback_enabled():
    settings = Settings(
        search_provider="tavily",
        tavily_api_key="test-key",
        allow_search_fallback=True,
    )
    service = SearchService(settings=settings)

    with patch.object(
        TavilySearchProvider,
        "search",
        AsyncMock(side_effect=httpx.HTTPError("Tavily down")),
    ):
        results = await service.search("AI chips")

    assert len(results) >= 1
    assert results[0]["raw_metadata"]["provider"] == "mock"


@pytest.mark.asyncio
async def test_tavily_failure_raises_when_fallback_disabled():
    settings = Settings(
        search_provider="tavily",
        tavily_api_key="test-key",
        allow_search_fallback=False,
    )
    service = SearchService(settings=settings)

    with patch.object(
        TavilySearchProvider,
        "search",
        AsyncMock(side_effect=httpx.HTTPError("Tavily down")),
    ):
        with pytest.raises(SearchProviderError):
            await service.search("AI chips")


@pytest.mark.asyncio
async def test_tavily_invalid_api_key_error():
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    provider = TavilySearchProvider("bad-key")

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(SearchProviderError, match="Invalid API key"):
            await provider.search("test query")


@pytest.mark.asyncio
async def test_search_agent_deduplicates_urls():
    from app.agents.search_agent import SearchAgent

    agent = SearchAgent()
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(
        side_effect=[
            [
                {
                    "title": "A",
                    "url": "https://example.com/article/?utm_source=a",
                    "snippet": "one",
                },
                {
                    "title": "B",
                    "url": "https://www.example.com/article",
                    "snippet": "dup",
                },
            ],
            [],
        ]
    )
    agent.search_service = mock_service

    results = await agent.run(
        questions=[{"question": "Q1", "priority": 1}],
        topic="Test",
    )

    assert len(results) == 1
    assert results[0]["citation_key"] == "S1"
