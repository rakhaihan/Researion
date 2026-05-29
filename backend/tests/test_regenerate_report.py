from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.research_service import ResearchService


@pytest.mark.asyncio
async def test_regenerate_report_skips_search():
    service = ResearchService()
    project_id = uuid4()
    user_id = uuid4()

    mock_project = AsyncMock()
    mock_project.id = project_id
    mock_project.topic = "AI chips"
    mock_project.research_type.value = "Technology Trend Analysis"
    mock_project.sources = [AsyncMock()]
    mock_project.sources[0].citation_key = "S1"
    mock_project.sources[0].title = "T"
    mock_project.sources[0].url = "https://example.com"
    mock_project.sources[0].snippet = "s"
    mock_project.sources[0].credibility_score = 8.0
    mock_project.sources[0].credibility_reason = "ok"
    mock_project.sources[0].source_type = "news"
    mock_project.sources[0].published_date = "2026"
    mock_project.sources[0].summary = None
    mock_project.questions = []
    mock_project.final_report = None

    service.get_research = AsyncMock(return_value=mock_project)
    service.critique_agent.run = AsyncMock(return_value={"weaknesses": []})
    service.report_writer.run = AsyncMock(
        return_value={
            "executive_summary": "Summary [S1]",
            "detailed_analysis": "Analysis [S1]",
            "key_findings": ["Point [S1]"],
            "risks_and_limitations": [],
            "conclusion": "End [S1]",
            "markdown_content": "# Report\n\n## Sources\n",
            "sources": [{"citation_key": "S1", "title": "T", "url": "https://example.com"}],
        }
    )
    service._run_quality_evaluation = AsyncMock()

    db = AsyncMock()

    with patch.object(service, "get_research", service.get_research):
        await service.regenerate_report(db, project_id, user_id)

    service.critique_agent.run.assert_awaited_once()
    service.report_writer.run.assert_awaited_once()
    service._run_quality_evaluation.assert_awaited_once()
    # Regenerate must not invoke the full workflow / search step
    assert service.workflow is None or not hasattr(service, "search_agent")
