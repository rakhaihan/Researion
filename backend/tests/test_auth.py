from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.api.deps import get_db, resolve_current_user
from app.core.config import get_settings
from app.core.jwt import create_access_token
from app.core.password import hash_password
from app.db.models import ResearchDepth, ResearchProject, ResearchStatus, ResearchType, User
from app.main import app
from app.services.auth_service import AuthService
from app.services.user_service import UserService


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _make_user(email: str = "usera@test.com") -> User:
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


@pytest.mark.asyncio
async def test_register_success():
    auth = AuthService()
    auth.user_service.create_user = AsyncMock(return_value=_make_user())
    db = AsyncMock()

    from app.schemas.auth import RegisterRequest

    result = await auth.register(
        db,
        RegisterRequest(full_name="Test", email="a@test.com", password="password123"),
    )
    assert result.access_token
    assert result.user.email == "usera@test.com"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails():
    user_service = UserService()
    db = AsyncMock()
    user_service.get_by_email = AsyncMock(return_value=_make_user())

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await user_service.create_user(db, "Test", "a@test.com", "password123")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_login_success():
    user = _make_user()
    auth = AuthService()
    auth.user_service.get_by_email = AsyncMock(return_value=user)
    db = AsyncMock()

    from app.schemas.auth import LoginRequest

    result = await auth.login(
        db,
        LoginRequest(email="usera@test.com", password="password123"),
    )
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails():
    user = _make_user()
    auth = AuthService()
    auth.user_service.get_by_email = AsyncMock(return_value=user)
    db = AsyncMock()

    from fastapi import HTTPException

    from app.schemas.auth import LoginRequest

    with pytest.raises(HTTPException) as exc:
        await auth.login(
            db,
            LoginRequest(email="usera@test.com", password="wrongpass9"),
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token():
    user = _make_user()

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[resolve_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {create_access_token(str(user.id))}"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.asyncio
async def test_research_without_token_fails_when_jwt_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "jwt")
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/research")

    get_settings.cache_clear()
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_research():
    from fastapi import HTTPException

    from app.services.research_service import ResearchService

    user_a = uuid4()
    user_b = uuid4()
    research_id = uuid4()

    ResearchProject(
        id=research_id,
        user_id=user_b,
        topic="Secret",
        research_type=ResearchType.MARKET_RESEARCH,
        depth=ResearchDepth.STANDARD,
        status=ResearchStatus.PENDING,
    )

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    service = ResearchService()
    with pytest.raises(HTTPException) as exc:
        await service.get_research(db, research_id, user_id=user_a)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_research_assigns_current_user():
    from app.schemas.research import ResearchCreate
    from app.schemas.research import ResearchDepth as RD
    from app.schemas.research import ResearchType as RT
    from app.services.research_service import ResearchService

    user_id = uuid4()
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    service = ResearchService()
    service.workspace_service.get_default_workspace_id = AsyncMock(return_value=uuid4())
    payload = ResearchCreate(
        topic="Test topic for research",
        research_type=RT.MARKET_RESEARCH,
        depth=RD.STANDARD,
    )
    project = await service.create_research(db, payload, user_id)
    assert project.user_id == user_id


def test_jwt_token_contains_subject():
    user_id = uuid4()
    token = create_access_token(str(user_id))
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == str(user_id)


def test_alembic_migration_files_exist():
    from pathlib import Path

    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    files = list(versions.glob("*.py"))
    assert len(files) >= 1
