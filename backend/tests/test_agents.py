import pytest

from app.agents.planner_agent import PlannerAgent
from app.services.search_service import MockSearchProvider
from app.utils.validators import sanitize_filename, validate_topic


@pytest.mark.asyncio
async def test_planner_agent_fallback_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")

    agent = PlannerAgent()
    questions = await agent.run(
        topic="NVIDIA stock outlook",
        research_type="Stock/Crypto Research",
        depth="standard",
    )

    assert len(questions) >= 3
    assert all("question" in q for q in questions)
    assert all("priority" in q for q in questions)


@pytest.mark.asyncio
async def test_mock_search_provider():
    provider = MockSearchProvider()
    results = await provider.search("AI startups 2026", max_results=2)

    assert len(results) == 2
    assert results[0]["url"].startswith("https://")


def test_validate_topic():
    assert validate_topic("  Valid topic  ") == "Valid topic"


def test_validate_topic_too_short():
    with pytest.raises(ValueError):
        validate_topic("ab")


def test_sanitize_filename():
    assert sanitize_filename("Analyze NVIDIA stock!!!") == "analyze-nvidia-stock"
