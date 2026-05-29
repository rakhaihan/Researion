from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Researion"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api"

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
        default="change-me-use-a-long-random-secret-in-production",
        description="JWT signing secret",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    api_key: str | None = Field(default=None, description="Required when AUTH_MODE=api_key")

    dev_user_email: str = "dev@researion.local"
    dev_user_password: str = "devpassword123"
    dev_user_full_name: str = "Development User"

    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    max_search_results: int = 5
    min_credibility_score: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
