from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
import respx
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import ConnectorAccount, User, UserLLMCredential


@pytest.mark.asyncio
async def test_api_health(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_api_auth(anon_client: AsyncClient) -> None:
    # Register
    reg_resp = await anon_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newdev@example.com",
            "display_name": "New Developer",
            "password": "SecurePassword123!",
        },
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "newdev@example.com"

    # Token (OAuth2 form)
    token_resp = await anon_client.post(
        "/api/v1/auth/token",
        data={
            "username": "newdev@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert token_resp.status_code == 200
    token_data = token_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert "social_manager_session" in token_resp.cookies

    # The browser can authenticate with the HTTP-only session cookie.
    me_resp = await anon_client.get("/api/v1/users/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newdev@example.com"

    logout_resp = await anon_client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 204
    assert (await anon_client.get("/api/v1/users/me")).status_code == 401


@pytest.mark.asyncio
async def test_api_users_me(client: AsyncClient, test_user: User) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_api_user_llm_credential(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    initial = await client.get("/api/v1/users/me/llm-credential")
    assert initial.status_code == 200
    assert initial.json() == {
        "configured": False,
        "provider": None,
        "key_hint": None,
        "updated_at": None,
    }

    plaintext_key = "test-user-gemini-api-key-9876"
    saved = await client.put(
        "/api/v1/users/me/llm-credential",
        json={"provider": "gemini", "api_key": plaintext_key},
    )
    assert saved.status_code == 200
    assert saved.json()["configured"] is True
    assert saved.json()["provider"] == "gemini"
    assert saved.json()["key_hint"] == "9876"
    assert "api_key" not in saved.json()

    stored = await db_session.scalar(
        select(UserLLMCredential).where(UserLLMCredential.user_id == test_user.id)
    )
    assert stored is not None
    assert stored.encrypted_api_key != plaintext_key
    assert plaintext_key not in stored.encrypted_api_key

    read_back = await client.get("/api/v1/users/me/llm-credential")
    assert read_back.status_code == 200
    assert read_back.json()["key_hint"] == "9876"
    assert "api_key" not in read_back.json()

    deleted = await client.delete("/api/v1/users/me/llm-credential")
    assert deleted.status_code == 204
    after_delete = await client.get("/api/v1/users/me/llm-credential")
    assert after_delete.json()["configured"] is False


@pytest.mark.asyncio
async def test_api_goals(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/goals",
        json={
            "title": "Gain visibility in open source",
            "description": "Target maintainer feedback and DevRel roles.",
            "target_audiences": ["DevRel managers", "Maintainers"],
            "priority": 60,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Gain visibility in open source"

    get_resp = await client.get("/api/v1/goals")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) >= 1


@pytest.mark.asyncio
async def test_api_memory_crud(client: AsyncClient) -> None:
    # 1. Create memory
    resp = await client.post(
        "/api/v1/memory",
        json={
            "category": "technical_knowledge",
            "title": "LangGraph Checkpoints",
            "statement": "Stateful execution via checkpoints enables human review interrupts.",
            "evidence_status": "user_confirmed",
            "visibility": "approved_public",
        },
    )
    assert resp.status_code == 201
    mem = resp.json()
    mem_id = mem["id"]

    # 2. Get memory
    get_resp = await client.get(f"/api/v1/memory/{mem_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == mem_id

    # 3. List memory
    list_resp = await client.get("/api/v1/memory?category=technical_knowledge")
    assert list_resp.status_code == 200
    assert any(m["id"] == mem_id for m in list_resp.json())

    # 4. Patch memory
    patch_resp = await client.patch(
        f"/api/v1/memory/{mem_id}",
        json={"title": "Updated LangGraph Checkpoints"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated LangGraph Checkpoints"

    # 5. Create another memory and link them
    m2 = (
        await client.post(
            "/api/v1/memory",
            json={
                "category": "project_contribution",
                "title": "Built LangGraph Workflow",
                "statement": "Built end-to-end LangGraph pipeline with review interrupts.",
                "evidence_status": "observed",
                "visibility": "potentially_shareable",
            },
        )
    ).json()

    link_resp = await client.post(
        "/api/v1/memory/links",
        json={
            "from_record_id": mem_id,
            "to_record_id": m2["id"],
            "relation": "supports",
        },
    )
    assert link_resp.status_code == 201

    # 6. Delete memory
    del_resp = await client.delete(f"/api/v1/memory/{mem_id}")
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_api_content(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/content",
        json={
            "platform": "user",
            "external_id": "manual_note_01",
            "content_type": "other",
            "title": "Notes on System Design",
            "body": "Detailed thoughts on caching and persistence models.",
            "is_own": True,
            "access_method": "user_provided",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["external_id"] == "manual_note_01"

    list_resp = await client.get("/api/v1/content?platform=user")
    assert list_resp.status_code == 200
    assert any(c["external_id"] == "manual_note_01" for c in list_resp.json())


@pytest.mark.asyncio
@respx.mock
async def test_api_connectors(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    respx.post("https://github.com/login/oauth/access_token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "gho_test_oauth_token",
                "scope": "read:user user:email",
            },
        )
    )
    respx.get("https://api.github.com/user").mock(
        return_value=Response(200, json={"id": 123, "login": "octo"})
    )
    respx.get("https://api.github.com/user/repos").mock(
        return_value=Response(
            200,
            json=[
                {
                    "id": 55,
                    "name": "my-tool",
                    "full_name": "octo/my-tool",
                    "description": "cool tool",
                    "html_url": "https://github.com/octo/my-tool",
                    "stargazers_count": 10,
                    "forks_count": 1,
                    "language": "Python",
                    "topics": [],
                    "updated_at": "2026-09-01T12:00:00Z",
                    "owner": {"login": "octo"},
                }
            ],
        )
    )

    # 1. Authorize endpoint
    auth_resp = await client.post("/api/v1/connectors/github/authorize")
    assert auth_resp.status_code == 200
    authorization_url = auth_resp.json()["authorization_url"]
    oauth_state = parse_qs(urlparse(authorization_url).query)["state"][0]

    # 2. Complete the provider login. State maps the callback to this app user.
    callback_resp = await client.get(
        "/api/v1/connectors/github/callback",
        params={"code": "github_oauth_code", "state": oauth_state},
        follow_redirects=False,
    )
    assert callback_resp.status_code == 303
    assert callback_resp.headers["location"] == (
        "http://localhost:3000/connectors?platform=github&result=success"
    )
    connected_account = await db_session.scalar(
        select(ConnectorAccount).where(
            ConnectorAccount.platform == "github",
            ConnectorAccount.user_id == test_user.id,
        )
    )
    assert connected_account is not None

    # 3. List connectors
    list_resp = await client.get("/api/v1/connectors")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 4. Sync connector
    sync_resp = await client.post("/api/v1/connectors/github/sync")
    assert sync_resp.status_code == 200
    assert sync_resp.json()["fetched"] == 1


@pytest.mark.asyncio
async def test_api_workflows_and_recommendations(client: AsyncClient) -> None:
    import uuid

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    # Seed a shareable technical memory so recommendations target a social platform
    await client.post(
        "/api/v1/memory",
        json={
            "category": "technical_knowledge",
            "title": "Async Microservices Architecture",
            "statement": "Designed event-driven async workers with high throughput.",
            "evidence_status": "user_confirmed",
            "visibility": "approved_public",
        },
    )

    # Start recommendation workflow
    start_resp = await client.post(
        "/api/v1/workflows/start",
        json={
            "kind": "recommendation_review",
            "thread_id": thread_id,
            "input": {"topic": "Async Microservices"},
        },
    )
    assert start_resp.status_code == 201
    run_data = start_resp.json()["run"]
    assert run_data["status"] == "interrupted"

    # List recommendations
    recs_resp = await client.get("/api/v1/recommendations?status=awaiting_review")
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    assert len(recs) >= 1
    rec_id = recs[0]["id"]

    # Review recommendation
    review_resp = await client.post(
        f"/api/v1/recommendations/{rec_id}/review",
        json={
            "decision": "approve",
            "scope": "this_only",
        },
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "approved"

    # Report performed
    perf_resp = await client.post(
        f"/api/v1/recommendations/{rec_id}/performed",
        json={
            "public_url": "https://x.com/status/987654",
            "external_id": "987654",
            "notes": "Published successfully",
        },
    )
    assert perf_resp.status_code == 200
    action_id = perf_resp.json()["id"]

    # Add metrics
    metric_resp = await client.post(
        f"/api/v1/recommendations/actions/{action_id}/metrics",
        json={
            "metrics": {"impressions": 1500, "likes": 50},
            "source": "api",
        },
    )
    assert metric_resp.status_code == 201
    assert metric_resp.json()["metric_snapshot_id"] is not None

    # Resume the workflow
    resume_resp = await client.post(
        f"/api/v1/workflows/{thread_id}/resume",
        json={
            "value": {
                "decision": "approve",
                "final_text": "Approved post",
                "scope": "this_only",
            }
        },
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["run"]["status"] == "completed"


@pytest.mark.asyncio
async def test_api_strategies(client: AsyncClient) -> None:
    # Get current strategy
    curr_resp = await client.get("/api/v1/strategies/current")
    assert curr_resp.status_code in {200, 404}

    # List strategies
    list_resp = await client.get("/api/v1/strategies")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)


@pytest.mark.asyncio
async def test_api_scheduler(client: AsyncClient) -> None:
    # Check scheduler status
    status_resp = await client.get("/api/v1/scheduler/status")
    assert status_resp.status_code == 200
    assert "is_running" in status_resp.json()

    # Trigger scheduler run manually
    run_resp = await client.post("/api/v1/scheduler/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "success"
    assert "result" in run_resp.json()
