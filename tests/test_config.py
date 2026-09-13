from __future__ import annotations

import pytest

from social_manager.config import Settings
from social_manager.db.session import Database


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_postgres_database_url_uses_async_psycopg_driver(scheme: str) -> None:
    settings = Settings(
        database_url=(
            f"{scheme}user:password@ep-example.us-east-2.aws.neon.tech/app"
            "?sslmode=require"
        ),
        checkpoint_database_url="postgresql://checkpoint-url-must-not-change",
    )

    assert settings.database_url == (
        "postgresql+psycopg://user:password@ep-example.us-east-2.aws.neon.tech/app"
        "?sslmode=require"
    )
    assert settings.checkpoint_database_url == "postgresql://checkpoint-url-must-not-change"

    database = Database(settings)
    assert database.engine.dialect.name == "postgresql"
    assert database.engine.dialect.driver == "psycopg"


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite+aiosqlite:///./test.db",
        "postgresql+psycopg://user:password@localhost/app",
    ],
)
def test_explicit_database_driver_is_preserved(database_url: str) -> None:
    assert Settings(database_url=database_url).database_url == database_url
