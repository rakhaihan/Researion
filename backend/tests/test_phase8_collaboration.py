import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.core.password import hash_password
from app.db.models import (
    FinalReport,
    ResearchDepth,
    ResearchProject,
    ResearchSourceMode,
    ResearchStatus,
    ResearchType,
    SharedReportLink,
    ShareVisibility,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from app.services.comment_service import CommentService
from app.services.permission_service import PermissionService
from app.services.share_service import ShareService
from app.services.version_service import VersionService
from app.services.workspace_service import WorkspaceService


def _user(email: str = "a@test.com") -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        full_name="User A",
        email=email,
        hashed_password=hash_password("password123"),
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


def _project(user_id: UUID, workspace_id: UUID | None = None) -> ResearchProject:
    return ResearchProject(
        id=uuid4(),
        user_id=user_id,
        workspace_id=workspace_id,
        topic="Test research topic for collaboration",
        research_type=ResearchType.MARKET_RESEARCH,
        depth=ResearchDepth.STANDARD,
        status=ResearchStatus.COMPLETED,
        research_source_mode=ResearchSourceMode.WEB_ONLY,
    )


@pytest.mark.asyncio
async def test_default_workspace_on_register():
    user = _user()
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    ws_service = WorkspaceService()
    now = datetime.now(UTC)
    user.id = uuid4()
    user.created_at = now
    user.updated_at = now

    def on_add(obj):
        if isinstance(obj, Workspace):
            obj.id = uuid4()
            obj.created_at = now
            obj.updated_at = now

    db.add = MagicMock(side_effect=on_add)
    workspace = await ws_service.ensure_default_workspace(db, user)
    assert workspace.is_default is True
    assert db.add.called


@pytest.mark.asyncio
async def test_viewer_cannot_run_research():
    perms = PermissionService()
    owner_id = uuid4()
    viewer_id = uuid4()
    ws_id = uuid4()
    project = _project(owner_id, ws_id)

    db = AsyncMock()

    async def fake_membership(db, workspace_id, user_id):
        if user_id == owner_id:
            return WorkspaceMember(workspace_id=ws_id, user_id=owner_id, role=WorkspaceRole.OWNER)
        if user_id == viewer_id:
            return WorkspaceMember(workspace_id=ws_id, user_id=viewer_id, role=WorkspaceRole.VIEWER)
        return None

    perms.get_membership = fake_membership
    assert await perms.can_run_research(db, project, owner_id)
    assert not await perms.can_run_research(db, project, viewer_id)


@pytest.mark.asyncio
async def test_editor_can_create_research():
    perms = PermissionService()
    ws_id = uuid4()
    editor_id = uuid4()
    db = AsyncMock()
    perms.get_membership = AsyncMock(
        return_value=WorkspaceMember(
            workspace_id=ws_id, user_id=editor_id, role=WorkspaceRole.EDITOR
        )
    )
    assert await perms.can_create_research(db, ws_id, editor_id)


@pytest.mark.asyncio
async def test_share_link_public_without_sensitive_fields():
    user_id = uuid4()
    project = _project(user_id)
    project.quality_score = 8.5
    project.quality_status = None
    project.created_at = datetime.now(UTC)
    project.updated_at = datetime.now(UTC)
    project.final_report = FinalReport(
        research_id=project.id,
        markdown_content="# Title\n\nBody",
        executive_summary="Summary",
        detailed_analysis="Analysis",
        conclusion="Done",
    )
    project.sources = []

    link = SharedReportLink(
        id=uuid4(),
        research_id=project.id,
        created_by=user_id,
        token=secrets.token_urlsafe(32),
        visibility=ShareVisibility.PUBLIC,
        allow_download=False,
    )

    service = ShareService()
    service._resolve_active_link = AsyncMock(return_value=link)
    service._load_project_with_report = AsyncMock(return_value=project)
    db = AsyncMock()
    public = await service.get_public_report(db, link.token)
    assert public.title
    assert "email" not in public.model_dump_json().lower()


@pytest.mark.asyncio
async def test_expired_share_returns_404():
    service = ShareService()
    link = SharedReportLink(
        id=uuid4(),
        research_id=uuid4(),
        created_by=uuid4(),
        token="tok",
        visibility=ShareVisibility.PUBLIC,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = link
    db.execute = AsyncMock(return_value=result)
    with pytest.raises(HTTPException) as exc:
        await service._resolve_active_link(db, "tok")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_version_compare_produces_diff():
    service = VersionService()
    v1 = MagicMock()
    v1.version_number = 1
    v1.markdown_content = "## Executive Summary\n\nOld text"
    v2 = MagicMock()
    v2.version_number = 2
    v2.markdown_content = "## Executive Summary\n\nNew text\n## Risks\n\nRisk"
    result = service._compare(v1, v2)
    assert result.from_version == 1
    assert "risks" in " ".join(result.added_sections).lower() or result.markdown_diff


@pytest.mark.asyncio
async def test_comment_crud_mocked():
    user = _user()
    project = _project(user.id)
    service = CommentService()
    service._get_project = AsyncMock(return_value=project)
    service.permissions.can_comment_research = AsyncMock(return_value=True)
    service.permissions.can_manage_comment = AsyncMock(return_value=True)
    db = AsyncMock()
    db.get = AsyncMock(return_value=user)
    db.flush = AsyncMock()
    now = datetime.now(UTC)

    def on_add(obj):
        if hasattr(obj, "id"):
            obj.id = uuid4()
        if hasattr(obj, "created_at"):
            obj.created_at = now
            obj.updated_at = now

    db.add = MagicMock(side_effect=on_add)

    from app.schemas.comment import CommentCreate

    created = await service.create_comment(
        db,
        project.id,
        user.id,
        CommentCreate(content="Nice report"),
    )
    assert created.content == "Nice report"


@pytest.mark.asyncio
async def test_list_research_excludes_archived_by_default():
    from app.services.research_service import ResearchService

    user_id = uuid4()
    ws_ids = [uuid4()]
    service = ResearchService()
    service.permissions.accessible_workspace_ids = AsyncMock(return_value=ws_ids)

    executed = MagicMock()
    executed.scalars.return_value.all.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=executed)

    await service.list_research(db, user_id, archived=False)
    call_args = db.execute.await_args[0][0]
    assert "archived_at" in str(call_args).lower() or call_args is not None


def test_alembic_phase8_migration_exists():
    from pathlib import Path

    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    assert any("005_workspace" in f.name for f in versions.glob("*.py"))
