from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.ext.asyncio import AsyncEngine

from social_manager.config import Settings


def configure_logging(environment: str) -> None:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    renderer: Any = (
        structlog.dev.ConsoleRenderer()
        if environment == "development"
        else structlog.processors.JSONRenderer()
    )
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_telemetry(
    app: FastAPI,
    engine: AsyncEngine,
    settings: Settings,
) -> TracerProvider | None:
    endpoint = settings.otel_exporter_otlp_endpoint
    if not endpoint:
        return None
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "social-media-manager-api",
                "deployment.environment": settings.app_env,
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    HTTPXClientInstrumentor().instrument(tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, tracer_provider=provider)
    return provider


def configure_langsmith(settings: Settings) -> None:
    """Configures LangSmith tracing environment variables when enabled."""
    import os

    if settings.langsmith_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_TRACING"] = "true"
        if settings.langsmith_api_key:
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key.get_secret_value()
            os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
