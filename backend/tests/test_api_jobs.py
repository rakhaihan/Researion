from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db, get_research_service
from app.db.models import JobStatus, ResearchJob, ResearchProject, ResearchStatus, ResearchType, ResearchDepth
from app.main import app
from app.schemas.job import ResearchProgressResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _make_project() -> ResearchProject:
    now = datetime.now(UTC)
    return ResearchProject(
        id=uuid4(),
        topic="NVIDIA stock outlook",
        research_type=ResearchType.STOCK_CRYPTO,
        depth=ResearchDepth.STANDARD,
        status=ResearchStatus.QUEUED,
        created_at=now,
        updated_at=now,
    )


def _make_job(project: ResearchProject) -> ResearchJob:
    now = datetime.now(UTC)
    return ResearchJob(
        id=uuid4(),
        research_id=project.id,
        job_id="api-test-job-id",
        status=JobStatus.QUEUED,
        current_step="planning",
        progress_percentage=0,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_run_endpoint_returns_job_id():
    project = _make_project()
    job = _make_job(project)

    mock_service = AsyncMock()
    mock_service.enqueue_research_run = AsyncMock(return_value=(project, job))

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_research_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/research/{project.id}/run")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["research_id"] == str(project.id)
    assert data["job_id"] == "api-test-job-id"
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_progress_endpoint_returns_status():
    project = _make_project()
    now = datetime.now(UTC)

    mock_service = AsyncMock()
    mock_service.job_service.get_progress = AsyncMock(
        return_value=ResearchProgressResponse(
            research_id=project.id,
            job_id="api-test-job-id",
            status=JobStatus.RUNNING,
            current_step="analyzing",
            current_step_label="Performing analysis",
            progress_percentage=70,
            error_message=None,
            updated_at=now,
        )
    )

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_research_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/research/{project.id}/progress")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["current_step"] == "analyzing"
    assert data["progress_percentage"] == 70
