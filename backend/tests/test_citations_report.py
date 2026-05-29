import pytest

from app.agents.report_writer_agent import ReportWriterAgent


def test_fallback_report_has_sources_section():
    agent = ReportWriterAgent()
    sources = [
        {
            "citation_key": "S1",
            "title": "NVIDIA Earnings",
            "url": "https://example.com/nvidia",
            "credibility_score": 8.5,
        },
        {
            "citation_key": "S2",
            "title": "Market Analysis",
            "url": "https://example.com/market",
            "credibility_score": 7.0,
        },
    ]
    report = agent._build_fallback_report(
        topic="NVIDIA outlook",
        research_type="Stock/Crypto Research",
        questions=[{"question": "What is the outlook?"}],
        analysis={
            "analysis": "Strong demand for AI accelerators [S1][S2].",
            "patterns": ["[S1] Data center growth continues."],
        },
        critique={"weaknesses": []},
        sources=sources,
    ).model_dump()
    markdown = agent._to_markdown(
        report, "NVIDIA outlook", "Stock/Crypto Research", sources
    )

    assert "## Sources" in markdown
    assert "[S1] NVIDIA Earnings — https://example.com/nvidia" in markdown
    assert "[S2] Market Analysis — https://example.com/market" in markdown
    assert "[S1]" in markdown.split("## Sources")[0]


@pytest.mark.asyncio
async def test_source_evaluator_credibility_reason_persisted_in_output():
    from app.agents.source_evaluator_agent import SourceEvaluatorAgent

    agent = SourceEvaluatorAgent()

    from app.schemas.agent_outputs import SourceEvaluationItem

    async def mock_generate_structured(system_prompt, user_prompt, model_type, fallback, **kwargs):
        return (
            SourceEvaluationItem(
                credibility_score=3.0,
                credibility_reason="Promotional blog with limited evidence.",
                source_type="blog",
                is_primary_source=False,
            ),
            [],
        )

    agent.llm.generate_structured = mock_generate_structured

    results = await agent.run(
        sources=[
            {
                "citation_key": "S1",
                "title": "Test Blog",
                "url": "https://blog.example.com/post",
                "snippet": "content",
                "question": "Q?",
            }
        ]
    )

    assert results[0]["credibility_reason"] == "Promotional blog with limited evidence."
    assert results[0]["credibility_score"] == 3.0
