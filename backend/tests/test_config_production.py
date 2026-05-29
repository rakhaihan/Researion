import pytest

from app.core.config import Settings


def test_production_rejects_disabled_auth():
    with pytest.raises(ValueError, match="AUTH_MODE=disabled"):
        Settings(
            environment="production",
            auth_mode="disabled",
            secret_key="x" * 32,
            backend_cors_origins="https://app.example.com",
            frontend_url="https://app.example.com",
        )


def test_production_requires_strong_secret():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            environment="production",
            auth_mode="jwt",
            secret_key="change-me-use-a-long-random-secret-in-production",
            backend_cors_origins="https://app.example.com",
            frontend_url="https://app.example.com",
        )
