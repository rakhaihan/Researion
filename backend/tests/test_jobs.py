from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.db.models import JobStatus, ResearchJob, ResearchProject, ResearchStatus, ResearchType, ResearchDepth
from app.schemas.job import JobStatus as SchemaJobStatus
from app.services.job_service import JobService


def _make_project(status=ResearchStatus.PENDING) -> ResearchProject:
    return ResearchProject(
        id=uuid4(),
        topic="NVIDIA stock outlook",
        research_type=ResearchType.STOCK_CRYPTO,
        depth=ResearchDepth.STANDARD,
        status=status,
    )


def _make_job(
    research_id,
    status=JobStatus.QUEUED,
    job_id: str | None = "arq-job-123",
) -> ResearchJob:
    now = datetime.now(UTC)
    return ResearchJob(
        id=uuid4(),
        research_id=research_id,
        job_id=job_id,
        status=status,
        current_step="planning",
        progress_percentage=0,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_enqueue_research_job_returns_job_with_job_id():
    service = JobService()
    project = _make_project()
    db = AsyncMock()

    active_result = MagicMock()
    active_result.scalar_one_or_none.return_value = None

    db.execute = AsyncMock(return_value=active_result)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_arq_job = MagicMock()
    mock_arq_job.job_id = "arq-job-abc"

    mock_pool = AsyncMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_arq_job)

    with patch("app.services.job_service.get_arq_pool", AsyncMock(return_value=mock_pool)):
        job = await service.enqueue_research_job(db, project)

    assert job.job_id == "arq-job-abc"
    assert job.status == JobStatus.QUEUED
    mock_pool.enqueue_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_enqueue_returns_existing_active_job_without_enqueue():
    service = JobService()
    project = _make_project(status=ResearchStatus.PLANNING)
    existing_job = _make_job(project.id, status=JobStatus.RUNNING, job_id="existing-job")

    active_result = MagicMock()
    active_result.scalar_one_or_none.return_value = existing_job

    db = AsyncMock()
    db.execute = AsyncMock(return_value=active_result)

    mock_pool = AsyncMock()

    with patch("app.services.job_service.get_arq_pool", AsyncMock(return_value=mock_pool)):
        job = await service.enqueue_research_job(db, project)

    assert job.job_id == "existing-job"
    assert job.status == JobStatus.RUNNING
    mock_pool.enqueue_job.assert_not_called()


@pytest.mark.asyncio
async def test_get_progress_returns_latest_status():
    service = JobService()
    research_id = uuid4()
    job = _make_job(research_id, status=JobStatus.RUNNING, job_id="job-progress-1")
    job.progress_percentage = 55
    job.current_step = "summarizing"
    job.error_message = None

    latest_result = MagicMock()
    latest_result.scalar_one_or_none.return_value = job

    db = AsyncMock()
    db.execute = AsyncMock(return_value=latest_result)

    user_id = uuid4()
    project_result = MagicMock()
    project_result.scalar_one_or_none.return_value = ResearchProject(
        id=research_id,
        user_id=user_id,
        topic="Test",
        research_type=ResearchType.STOCK_CRYPTO,
        depth=ResearchDepth.STANDARD,
        status=ResearchStatus.PENDING,
    )
    db.execute = AsyncMock(side_effect=[project_result, latest_result])

    progress = await service.get_progress(db, research_id, user_id)

    assert progress.research_id == research_id
    assert progress.job_id == "job-progress-1"
    assert progress.status == SchemaJobStatus.RUNNING
    assert progress.current_step == "summarizing"
    assert progress.progress_percentage == 55


@pytest.mark.asyncio
async def test_mark_failed_sets_failed_status():
    service = JobService()
    research_id = uuid4()
    job = _make_job(research_id, status=JobStatus.RUNNING)
    project = _make_project(status=ResearchStatus.PLANNING)
    project.id = research_id

    job_result = MagicMock()
    job_result.scalar_one_or_none.side_effect = [job, project]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=job_result)
    db.flush = AsyncMock()

    await service.mark_failed(db, job.id, "Workflow exploded")

    assert job.status == JobStatus.FAILED
    assert job.error_message == "Workflow exploded"
    assert project.status == ResearchStatus.FAILED
    assert project.error_message == "Workflow exploded"
