from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import SecretStr

from social_manager.config import Settings
from social_manager.db.session import database
from social_manager.observability import (
    configure_langsmith,
    configure_logging,
    configure_telemetry,
)


def test_configure_logging() -> None:
    # Should not raise
    configure_logging("development")
    configure_logging("production")


def test_configure_langsmith() -> None:
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key=SecretStr("lsv2_test_api_key_123"),
        langsmith_project="test-project",
    )
    configure_langsmith(settings)
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGSMITH_TRACING") == "true"
    assert os.environ.get("LANGSMITH_API_KEY") == "lsv2_test_api_key_123"
    assert os.environ.get("LANGSMITH_PROJECT") == "test-project"


def test_configure_telemetry_disabled() -> None:
    settings = Settings(otel_exporter_otlp_endpoint=None)
    app = FastAPI()
    provider = configure_telemetry(app, database.engine, settings)
    assert provider is None
