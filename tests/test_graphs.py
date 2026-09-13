from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.runtime import graph_runtime
from social_manager.db.models import ActionRecord, Recommendation, User
from social_manager.domain.enums import (
    ActionType,
    Platform,
    RecommendationStatus,
    WorkflowKind,
)
from social_manager.domain.schemas import WorkflowResume, WorkflowStart
from social_manager.services.workflows import WorkflowService


@pytest.mark.asyncio
async def test_workflow_a_profile_graph(db_session: AsyncSession, test_user: User) -> None:
    service = WorkflowService(graph_runtime)
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    # Start workflow A
    run, _ = await service.start(
        db_session,
        test_user.id,
        WorkflowStart(kind=WorkflowKind.PROFILE, thread_id=thread_id),
    )
    assert run.status == "interrupted"
    assert "items" in run.interrupt_data
    interrupt_payload = run.interrupt_data["items"][0]
    assert interrupt_payload.get("type") == "profile_baseline_review"

    # Resume with approval
    resumed_run, _ = await service.resume(
        db_session,
        test_user.id,
        thread_id,
        WorkflowResume(value={"decision": "approve"}),
    )
    assert resumed_run.status == "completed"


@pytest.mark.asyncio
async def test_workflow_b_daily_capture_graph(db_session: AsyncSession, test_user: User) -> None:
    service = WorkflowService(graph_runtime)
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    run, _ = await service.start(
        db_session,
        test_user.id,
        WorkflowStart(
            kind=WorkflowKind.DAILY_CAPTURE,
            thread_id=thread_id,
            input={
                "reflection": (
                    "Today I designed a robust scheduler for PostgreSQL and SQLite backends."
                )
            },
        ),
    )
    assert run.status == "completed"


@pytest.mark.asyncio
async def test_workflow_c_research_graph(db_session: AsyncSession, test_user: User) -> None:
    service = WorkflowService(graph_runtime)
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    run, _ = await service.start(
        db_session,
        test_user.id,
        WorkflowStart(
            kind=WorkflowKind.RESEARCH,
            thread_id=thread_id,
            input={"sources": []},
        ),
    )
    assert run.status == "completed"


@pytest.mark.asyncio
async def test_workflow_d_and_e_recommendation_review_graph(
    db_session: AsyncSession, test_user: User
) -> None:
    service = WorkflowService(graph_runtime)
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    run, _ = await service.start(
        db_session,
        test_user.id,
        WorkflowStart(
            kind=WorkflowKind.RECOMMENDATION_REVIEW,
            thread_id=thread_id,
            input={"topic": "Python Async Systems"},
        ),
    )
    assert run.status == "interrupted"

    # Resume with review decision
    resumed_run, _recs = await service.resume(
        db_session,
        test_user.id,
        thread_id,
        WorkflowResume(
            value={
                "decision": "approve",
                "final_text": "Approved post draft.",
                "scope": "this_only",
            }
        ),
    )
    assert resumed_run.status == "completed"


@pytest.mark.asyncio
async def test_workflow_f_outcome_strategy_graph(db_session: AsyncSession, test_user: User) -> None:
    service = WorkflowService(graph_runtime)
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"

    # Create recommendation and action record for outcome analysis
    rec = Recommendation(
        user_id=test_user.id,
        action_type=ActionType.ORIGINAL_POST.value,
        platform=Platform.X.value,
        status=RecommendationStatus.REPORTED_PERFORMED.value,
        title="Async Performance Insights",
        purpose="Share async lessons",
        target_audience="Backend Developers",
        why_now="Recent trend in async runtimes",
        draft="Async runtimes require careful task group management.",
    )
    db_session.add(rec)
    await db_session.commit()
    await db_session.refresh(rec)

    action = ActionRecord(
        user_id=test_user.id,
        recommendation_id=rec.id,
        status=RecommendationStatus.REPORTED_PERFORMED.value,
        performed_at=datetime.now(UTC),
        measurement_due_at=datetime.now(UTC),
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    run, _ = await service.start(
        db_session,
        test_user.id,
        WorkflowStart(
            kind=WorkflowKind.OUTCOME_STRATEGY,
            thread_id=thread_id,
            input={
                "action_id": action.id,
                "metrics": {"impressions": 500, "likes": 20},
            },
        ),
    )
    assert run.status == "completed"
