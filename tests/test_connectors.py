from __future__ import annotations

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.connectors.github import GitHubConnector
from social_manager.connectors.linkedin import LinkedInConnector
from social_manager.connectors.x import XConnector
from social_manager.db.models import User
from social_manager.domain.enums import ConnectorStatus, Platform
from social_manager.domain.schemas import ConnectorTokenInput
from social_manager.services.connectors import ConnectorService


@pytest.mark.asyncio
@respx.mock
async def test_github_connector() -> None:
    respx.get("https://api.github.com/user").mock(
        return_value=Response(
            200,
            json={
                "id": 987654,
                "login": "octocat",
                "name": "The Octocat",
                "html_url": "https://github.com/octocat",
                "public_repos": 8,
                "followers": 150,
            },
        )
    )
    respx.get("https://api.github.com/user/repos").mock(
        return_value=Response(
            200,
            json=[
                {
                    "id": 101,
                    "name": "super-fastapi",
                    "full_name": "octocat/super-fastapi",
                    "description": "FastAPI extension for async tasks",
                    "html_url": "https://github.com/octocat/super-fastapi",
                    "stargazers_count": 25,
                    "forks_count": 4,
                    "language": "Python",
                    "topics": ["fastapi", "python"],
                    "updated_at": "2026-09-01T12:00:00Z",
                    "owner": {"login": "octocat"},
                }
            ],
        )
    )

    connector = GitHubConnector(access_token="gho_mock_token")
    identity = await connector.get_identity()
    assert identity.external_user_id == "987654"
    assert identity.username == "octocat"

    batch = await connector.sync_own_content()
    assert len(batch.content) == 1
    item = batch.content[0]
    assert item.platform == Platform.GITHUB
    assert item.external_id == "repo:101"
    assert item.normalized_data["name"] == "super-fastapi"


@pytest.mark.asyncio
@respx.mock
async def test_x_connector() -> None:
    respx.get("https://api.x.com/2/users/me").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "id": "123456789",
                    "username": "techdev",
                    "name": "Tech Developer",
                    "description": "Building cool async tools",
                    "public_metrics": {"followers_count": 500},
                }
            },
        )
    )
    respx.get("https://api.x.com/2/users/123456789/tweets").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "tweet_1",
                        "text": "Async Python 3.12 tips and tricks thread.",
                        "created_at": "2026-09-10T10:00:00Z",
                        "public_metrics": {
                            "impression_count": 2500,
                            "like_count": 65,
                            "retweet_count": 12,
                        },
                    }
                ],
                "meta": {"result_count": 1},
            },
        )
    )

    connector = XConnector(access_token="mock_x_token")
    identity = await connector.get_identity()
    assert identity.external_user_id == "123456789"
    assert identity.username == "techdev"

    batch = await connector.sync_own_content()
    assert len(batch.content) == 1
    assert batch.content[0].platform == Platform.X
    assert batch.content[0].body == "Async Python 3.12 tips and tricks thread."


@pytest.mark.asyncio
@respx.mock
async def test_linkedin_connector() -> None:
    respx.get("https://api.linkedin.com/v2/userinfo").mock(
        return_value=Response(
            200,
            json={
                "sub": "linkedin_user_999",
                "name": "Jane Developer",
                "given_name": "Jane",
                "family_name": "Developer",
            },
        )
    )
    respx.get("https://api.linkedin.com/rest/posts").mock(
        return_value=Response(
            200,
            json={
                "elements": [
                    {
                        "id": "li_post_555",
                        "commentary": {"text": "Excited to share our open source milestone!"},
                        "createdAt": 1726000000000,
                        "lifecycleState": "PUBLISHED",
                        "visibility": "PUBLIC",
                    }
                ],
                "paging": {"start": 0, "count": 1, "total": 1},
            },
        )
    )

    connector = LinkedInConnector(access_token="mock_li_token")
    identity = await connector.get_identity()
    assert identity.external_user_id == "linkedin_user_999"
    assert identity.display_name == "Jane Developer"

    batch = await connector.sync_own_content()
    assert len(batch.content) == 1
    item = batch.content[0]
    assert item.platform == Platform.LINKEDIN
    assert item.body == "Excited to share our open source milestone!"


@pytest.mark.asyncio
@respx.mock
async def test_connector_service_sync_and_retention(
    db_session: AsyncSession, test_user: User
) -> None:
    # Mock LinkedIn endpoints
    respx.get("https://api.linkedin.com/v2/userinfo").mock(
        return_value=Response(
            200,
            json={"sub": "li_sub_123", "name": "LinkedIn User"},
        )
    )
    respx.get("https://api.linkedin.com/rest/posts").mock(
        return_value=Response(
            200,
            json={
                "elements": [
                    {
                        "id": "post_789",
                        "commentary": "Reflecting on engineering leadership.",
                        "createdAt": 1726000000000,
                    }
                ],
                "paging": {"start": 0, "count": 1, "total": 1},
            },
        )
    )

    service = ConnectorService()
    # Save token manually
    account = await service.connect_token(
        db_session,
        test_user.id,
        Platform.LINKEDIN,
        ConnectorTokenInput(access_token="mock_access_token"),
    )
    assert account.status == ConnectorStatus.CONNECTED.value

    # Sync
    result = await service.sync(db_session, test_user.id, Platform.LINKEDIN)
    assert result.fetched == 1
    assert result.created == 1

    # Verify conservative retention was set on LinkedIn content
    from sqlalchemy import select

    from social_manager.db.models import PlatformContent

    stmt = select(PlatformContent).where(
        PlatformContent.user_id == test_user.id,
        PlatformContent.platform == Platform.LINKEDIN.value,
    )
    saved_content = await db_session.scalar(stmt)
    assert saved_content is not None
    assert saved_content.retention_expires_at is not None
