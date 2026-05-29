from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "change-me-use-a-long-random-secret-in-production"


def _parse_origins(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("["):
        import json

        parsed = json.loads(raw)
        return [str(item).strip() for item in parsed]
    return [part.strip() for part in raw.split(",") if part.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Researion"
    app_version: str = "1.0.0"
    environment: Literal["development", "production", "test"] = Field(
        default="development",
        description="Runtime environment",
    )
    debug: bool = False
    api_prefix: str = "/api"
    log_json: bool = Field(
        default=False,
        description="Emit structured JSON logs (auto-enabled in production)",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/researion",
        description="Async PostgreSQL connection string",
    )
    auto_create_tables: bool = Field(
        default=False,
        description="Use create_all on startup (dev only; prefer Alembic in production)",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for background job queue",
    )

    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Default LLM model")
    llm_provider: Literal["openai"] = "openai"
    llm_temperature: float = 0.2

    search_provider: Literal["tavily", "serpapi", "mock"] = "mock"
    tavily_api_key: str = ""
    tavily_max_results: int = Field(default=5, description="Max results per Tavily query")
    serpapi_api_key: str = ""
    allow_search_fallback: bool = Field(
        default=True,
        description="Fall back to mock search when live provider fails",
    )

    auth_mode: Literal["jwt", "api_key", "disabled"] = Field(
        default="disabled",
        description="jwt | api_key | disabled (local dev bypass)",
    )
    secret_key: str = Field(
        default=DEFAULT_SECRET,
        description="JWT signing secret",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    api_key: str | None = Field(default=None, description="Required when AUTH_MODE=api_key")
    admin_api_key: str | None = Field(
        default=None,
        description="Optional key for admin maintenance endpoints",
    )

    dev_user_email: str = "dev@researion.local"
    dev_user_password: str = "devpassword123"
    dev_user_full_name: str = "Development User"

    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Public frontend URL (no trailing slash)",
    )
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated CORS origins",
    )

    max_search_results: int = 5
    min_credibility_score: float = 5.0

    max_request_body_bytes: int = Field(default=1_048_576, description="Max HTTP body size (1MB)")
    auth_rate_limit: str = Field(default="10/minute", description="Rate limit for auth endpoints")

    gunicorn_workers: int = Field(default=2, description="Uvicorn workers under Gunicorn")

    @property
    def cors_origins(self) -> list[str]:
        origins = _parse_origins(self.backend_cors_origins)
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url.rstrip("/"))
        return origins

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("frontend_url")
    @classmethod
    def strip_frontend_url(cls, value: str) -> str:
        return value.rstrip("/")

    @model_validator(mode="after")
    def apply_production_defaults(self) -> "Settings":
        if self.environment == "production":
            object.__setattr__(self, "log_json", True)
            object.__setattr__(self, "debug", False)
        return self

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment != "production":
            return self

        if self.auth_mode == "disabled":
            raise ValueError("AUTH_MODE=disabled is not allowed when ENVIRONMENT=production")

        if self.secret_key == DEFAULT_SECRET or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and not the default value "
                "when ENVIRONMENT=production"
            )

        if "localhost" in self.backend_cors_origins.lower() and len(self.cors_origins) <= 2:
            import warnings

            warnings.warn(
                "BACKEND_CORS_ORIGINS still references localhost in production",
                stacklevel=2,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
