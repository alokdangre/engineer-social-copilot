from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Social Media Manager"
    app_env: Literal["development", "test", "production"] = "development"
    app_secret_key: SecretStr = SecretStr("development-only-change-me")
    api_prefix: str = "/api/v1"
    access_token_minutes: int = 60
    database_url: str = "sqlite+aiosqlite:///./social_manager.db"
    checkpoint_database_url: str | None = None
    allowed_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost:3000"])

    llm_provider: Literal["gemini", "openai"] = "gemini"
    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openai_base_url: str | None = None
    reasoning_model: str = "gemini-2.5-flash"
    extraction_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    openai_reasoning_model: str = "gpt-4.1-mini"
    openai_extraction_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    model_fallback_enabled: bool = True

    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "social-media-manager-development"
    otel_exporter_otlp_endpoint: str | None = None

    github_client_id: str | None = None
    github_client_secret: SecretStr | None = None
    x_client_id: str | None = None
    x_client_secret: SecretStr | None = None
    linkedin_client_id: str | None = None
    linkedin_client_secret: SecretStr | None = None
    oauth_callback_base_url: str = "http://localhost:8000/api/v1/connectors"
    frontend_app_url: str = "http://localhost:3000"
    session_cookie_name: str = "social_manager_session"

    connector_timeout_seconds: float = 20.0
    connector_max_retries: int = 3
    default_research_retention_hours: int = 48
    max_daily_recommendations: int = 5

    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 300

    @field_validator("database_url", mode="before")
    @classmethod
    def use_async_postgres_driver(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def active_llm_api_key(self) -> SecretStr | None:
        if self.gemini_api_key is not None:
            return self.gemini_api_key
        return self.openai_api_key

    @property
    def active_llm_base_url(self) -> str | None:
        if self.openai_base_url:
            return self.openai_base_url
        if self.gemini_api_key is not None or self.llm_provider == "gemini":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        return None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    parsed = json.loads(trimmed)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in trimmed.split(",") if origin.strip()]
        return value

    @field_validator("app_secret_key")
    @classmethod
    def require_production_secret(cls, value: SecretStr, info: object) -> SecretStr:
        # Production validation is completed after the model is built in assert_safe_for_startup.
        return value

    def assert_safe_for_startup(self) -> None:
        if (
            self.app_env == "production"
            and self.app_secret_key.get_secret_value() == "development-only-change-me"
        ):
            raise RuntimeError("APP_SECRET_KEY must be set to a strong value in production")
        if self.app_env == "production":
            database_urls = [("DATABASE_URL", self.database_url)]
            if self.checkpoint_database_url:
                database_urls.append(
                    ("CHECKPOINT_DATABASE_URL", self.checkpoint_database_url)
                )
            for variable_name, database_url in database_urls:
                if make_url(database_url).host in {"localhost", "127.0.0.1", "::1"}:
                    raise RuntimeError(
                        f"{variable_name} cannot point to localhost in production; "
                        "set it to the externally reachable Neon Postgres URL"
                    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
