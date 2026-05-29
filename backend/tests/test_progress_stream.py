import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_research_service, resolve_current_user
from app.core.password import hash_password
from app.db.models import JobStatus, ResearchJob, ResearchProject, ResearchStatus, ResearchDepth, ResearchType, User
from app.main import app
from app.schemas.job import ResearchProgressResponse, ResearchStep


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _make_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        full_name="Stream User",
        email="stream@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_progress_stream_emits_events():
    research_id = uuid4()
    now = datetime.now(UTC)
    user = _make_user()

    progress_running = ResearchProgressResponse(
        research_id=research_id,
        job_id="stream-job",
        status=JobStatus.RUNNING,
        current_step=ResearchStep.PLANNING.value,
        current_step_label="Planning",
        progress_percentage=10,
        error_message=None,
        started_at=now,
        updated_at=now,
    )
    progress_done = progress_running.model_copy(
        update={
            "status": JobStatus.COMPLETED,
            "current_step": ResearchStep.COMPLETED.value,
            "progress_percentage": 100,
        }
    )

    mock_job_service = AsyncMock()
    mock_job_service.get_progress = AsyncMock(side_effect=[progress_running, progress_done])

    mock_service = AsyncMock()
    mock_service.job_service = mock_job_service

    app.dependency_overrides[get_research_service] = lambda: mock_service
    app.dependency_overrides[resolve_current_user] = lambda: user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/research/{research_id}/progress/stream",
                headers={"Authorization": "Bearer test"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            chunks = [line for line in response.text.split("\n") if line.startswith("data: ")]
            assert len(chunks) >= 2
            first = json.loads(chunks[0].replace("data: ", ""))
            assert first["status"] == "running"
            assert first["progress_percentage"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_progress_endpoint_still_available():
    """Ensure REST progress endpoint pattern is unchanged (mocked)."""
    research_id = uuid4()
    now = datetime.now(UTC)
    user = _make_user()

    progress = ResearchProgressResponse(
        research_id=research_id,
        job_id="job-1",
        status=JobStatus.QUEUED,
        current_step=ResearchStep.PLANNING.value,
        current_step_label="Planning",
        progress_percentage=0,
        error_message=None,
        started_at=None,
        updated_at=now,
    )

    mock_job_service = AsyncMock()
    mock_job_service.get_progress = AsyncMock(return_value=progress)
    mock_service = AsyncMock()
    mock_service.job_service = mock_job_service

    app.dependency_overrides[get_research_service] = lambda: mock_service
    app.dependency_overrides[resolve_current_user] = lambda: user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/research/{research_id}/progress")
            assert response.status_code == 200
            body = response.json()
            assert body["job_id"] == "job-1"
            assert body["progress_percentage"] == 0
    finally:
        app.dependency_overrides.clear()
