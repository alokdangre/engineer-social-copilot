from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from social_manager.agent.runtime import graph_runtime
from social_manager.api.routes import api_router
from social_manager.config import get_settings
from social_manager.db.session import database
from social_manager.observability import (
    configure_langsmith,
    configure_logging,
    configure_telemetry,
)
from social_manager.services.scheduler import app_scheduler


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app_env)
    configure_langsmith(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        settings.assert_safe_for_startup()
        await database.create_schema()
        await graph_runtime.initialize()
        await app_scheduler.start()
        yield
        await app_scheduler.stop()
        await graph_runtime.close()
        await database.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Human-reviewed AI social media and career manager for technical professionals"
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            settings.allowed_origins
            if isinstance(settings.allowed_origins, list)
            else [settings.allowed_origins]
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    configure_telemetry(app, database.engine, settings)
    return app


app = create_app()
