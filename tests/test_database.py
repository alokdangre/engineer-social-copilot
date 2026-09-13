from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import (
    ActionRecord,
    ConnectorAccount,
    DomainEvent,
    Hypothesis,
    MemoryLink,
    MemoryRecord,
    MetricSnapshot,
    PlatformContent,
    Recommendation,
    StrategyVersion,
    User,
)
from social_manager.domain.enums import (
    ActionType,
    ConnectorStatus,
    EvidenceStatus,
    MemoryCategory,
    Platform,
    RecommendationStatus,
    Visibility,
)


@pytest.mark.asyncio
async def test_database_model_crud(db_session: AsyncSession) -> None:
    # 1. Create a user
    user = User(
        email="dbuser@example.com",
        password_hash="fakehashedpassword",
        display_name="DB Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None

    # 2. Create memory with embedding
    memory = MemoryRecord(
        user_id=user.id,
        category=MemoryCategory.TECHNICAL_KNOWLEDGE.value,
        title="Async Python Architecture",
        statement="Detailed mastery of Python async IO event loops.",
        evidence_status=EvidenceStatus.USER_CONFIRMED.value,
        confidence=0.95,
        visibility=Visibility.APPROVED_PUBLIC.value,
        source_platform=Platform.USER.value,
        captured_at=datetime.now(UTC),
        embedding=[0.1, 0.2, 0.3, 0.4],
    )
    db_session.add(memory)
    await db_session.commit()
    await db_session.refresh(memory)
    assert memory.id is not None
    assert memory.embedding == [0.1, 0.2, 0.3, 0.4]

    # 3. Create a memory link
    memory2 = MemoryRecord(
        user_id=user.id,
        category=MemoryCategory.PROJECT_CONTRIBUTION.value,
        title="Async Project",
        statement="Built open source async pipeline.",
        evidence_status=EvidenceStatus.OBSERVED.value,
        confidence=0.9,
        visibility=Visibility.POTENTIALLY_SHAREABLE.value,
        source_platform=Platform.GITHUB.value,
        captured_at=datetime.now(UTC),
    )
    db_session.add(memory2)
    await db_session.commit()
    await db_session.refresh(memory2)

    link = MemoryLink(
        user_id=user.id,
        from_record_id=memory.id,
        to_record_id=memory2.id,
        relation="supports",
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    assert link.id is not None

    # 4. Create connector account
    connector = ConnectorAccount(
        user_id=user.id,
        platform=Platform.GITHUB.value,
        status=ConnectorStatus.CONNECTED.value,
        encrypted_access_token="encrypted_token_data",
        scopes=["read:user"],
    )
    db_session.add(connector)
    await db_session.commit()

    # 5. Create platform content
    content = PlatformContent(
        user_id=user.id,
        connector_id=connector.id,
        platform=Platform.GITHUB.value,
        external_id="repo:12345",
        content_type="repository",
        body="A repository about async Python",
        is_own=True,
        access_method="api",
        collected_at=datetime.now(UTC),
    )
    db_session.add(content)
    await db_session.commit()

    # 6. Recommendation and Action Record
    rec = Recommendation(
        user_id=user.id,
        action_type=ActionType.ORIGINAL_POST.value,
        platform=Platform.X.value,
        status=RecommendationStatus.AWAITING_REVIEW.value,
        title="Share Async Findings",
        purpose="Educate technical audience about async IO.",
        target_audience="Backend Engineers",
        why_now="Recent trend in async Python performance",
        draft="Here is what I learned building async engines in Python...",
    )
    db_session.add(rec)
    await db_session.commit()

    action = ActionRecord(
        user_id=user.id,
        recommendation_id=rec.id,
        status=RecommendationStatus.REPORTED_PERFORMED.value,
        performed_at=datetime.now(UTC),
        measurement_due_at=datetime.now(UTC),
    )
    db_session.add(action)
    await db_session.commit()

    # 7. Metric snapshot
    metric = MetricSnapshot(
        action_id=action.id,
        user_id=user.id,
        platform=Platform.X.value,
        captured_at=datetime.now(UTC),
        source="api",
        metrics={"impressions": 450, "likes": 12, "replies": 3},
    )
    db_session.add(metric)
    await db_session.commit()

    # 8. Strategy & Hypothesis
    strat = StrategyVersion(
        user_id=user.id,
        version=1,
        status="active",
        positioning="Async Python Specialist",
        content_pillars=["Async IO", "Architecture"],
        audience_priorities=["Backend Engineers"],
        platform_tactics={"x": "threads", "linkedin": "articles"},
        rationale="Strong background in distributed systems.",
    )
    db_session.add(strat)
    await db_session.commit()

    hyp = Hypothesis(
        user_id=user.id,
        strategy_version_id=strat.id,
        statement="Technical deep-dives generate more discussion than summaries.",
        observation="Posts with benchmarks get 3x comments.",
        target_audience="Senior Backend Engineers",
        expected_outcome="Increase in technical follower engagement.",
    )
    db_session.add(hyp)
    await db_session.commit()

    # 9. Domain Event
    event = DomainEvent(
        user_id=user.id,
        event_type="test_event_occurred",
        aggregate_type="test",
        aggregate_id="123",
        available_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.commit()

    # Query verification
    queried_user = await db_session.scalar(select(User).where(User.id == user.id))
    assert queried_user is not None
    assert queried_user.email == "dbuser@example.com"
