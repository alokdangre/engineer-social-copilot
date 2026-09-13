from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from social_manager.agent.runtime import graph_runtime
from social_manager.config import Settings, get_settings
from social_manager.db.base import Base
from social_manager.db.models import User
from social_manager.db.session import database
from social_manager.domain.schemas import UserCreate
from social_manager.main import app
from social_manager.security import create_access_token
from social_manager.services.users import UserService

TEST_DB_FILE = "./test_social_manager.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"


def get_test_settings() -> Settings:
    return Settings(
        app_env="test",
        app_secret_key=SecretStr("test-secret-key-32-chars-long-12345"),
        database_url=TEST_DATABASE_URL,
        checkpoint_database_url=None,
        scheduler_enabled=False,
        model_fallback_enabled=True,
        github_client_id="test_gh_client_id",
        github_client_secret=SecretStr("test_gh_client_secret"),
        x_client_id="test_x_client_id",
        x_client_secret=SecretStr("test_x_client_secret"),
        linkedin_client_id="test_li_client_id",
        linkedin_client_secret=SecretStr("test_li_client_secret"),
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_env() -> None:
    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["CHECKPOINT_DATABASE_URL"] = ""
    os.environ["APP_SECRET_KEY"] = "test-secret-key-32-chars-long-12345"
    os.environ["SCHEDULER_ENABLED"] = "false"
    os.environ["GITHUB_CLIENT_ID"] = "test_gh_client_id"
    os.environ["X_CLIENT_ID"] = "test_x_client_id"
    os.environ["LINKEDIN_CLIENT_ID"] = "test_li_client_id"
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database() -> AsyncIterator[None]:
    settings = get_test_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    database.settings = settings
    database.engine = engine
    database.session_factory = session_factory
    graph_runtime.settings = settings

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await graph_runtime.initialize()

    yield

    await graph_runtime.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    def _remove_file() -> None:
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except OSError:
                pass

    await asyncio.to_thread(_remove_file)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        yield session


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    existing = await db_session.scalar(select(User).where(User.email == "engineer@example.com"))
    if existing is not None:
        return existing
    return await UserService().create(
        db_session,
        UserCreate(
            email="engineer@example.com",
            display_name="Test Developer",
            password="SecurePassword123!",
        ),
    )


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    settings = get_test_settings()
    token = create_access_token(test_user.id, settings=settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(test_user: User) -> AsyncIterator[AsyncClient]:
    settings = get_test_settings()
    app.dependency_overrides = {}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {create_access_token(test_user.id, settings=settings)}"},
    ) as ac:
        yield ac


@pytest.fixture
async def anon_client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides = {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
