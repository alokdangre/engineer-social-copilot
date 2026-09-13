from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import (
    ActionRecord,
    ConnectorAccount,
    MemoryRecord,
    PlatformContent,
    Recommendation,
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
from social_manager.services.scheduler import AsyncScheduler, SchedulerService


@pytest.mark.asyncio
async def test_scheduler_purge_expired_retention(db_session: AsyncSession, test_user: User) -> None:
    service = SchedulerService()
    past_time = datetime.now(UTC) - timedelta(hours=10)

    # Expired content
    expired_content = PlatformContent(
        user_id=test_user.id,
        platform=Platform.LINKEDIN.value,
        external_id="exp_content_1",
        content_type="post",
        access_method="api",
        collected_at=past_time,
        retention_expires_at=past_time,
        is_own=False,
    )
    # Active content
    active_content = PlatformContent(
        user_id=test_user.id,
        platform=Platform.GITHUB.value,
        external_id="active_content_1",
        content_type="repository",
        access_method="api",
        collected_at=datetime.now(UTC),
        retention_expires_at=datetime.now(UTC) + timedelta(days=7),
        is_own=True,
    )
    # Expired memory
    expired_memory = MemoryRecord(
        user_id=test_user.id,
        category=MemoryCategory.READING_MEDIA.value,
        title="Temp Reading Note",
        statement="Note meant to be temporary.",
        evidence_status=EvidenceStatus.USER_CONFIRMED.value,
        source_platform=Platform.USER.value,
        captured_at=past_time,
        retention_expires_at=past_time,
        visibility=Visibility.PRIVATE.value,
    )
    db_session.add_all([expired_content, active_content, expired_memory])
    await db_session.commit()

    result = await service.purge_expired_retention(db_session)
    assert result["purged_content"] >= 1
    assert result["purged_memories"] >= 1

    # Verify expired_content was deleted from table
    check_content = await db_session.scalar(
        select(PlatformContent).where(PlatformContent.external_id == "exp_content_1")
    )
    assert check_content is None

    # Verify active content remains
    check_active = await db_session.scalar(
        select(PlatformContent).where(PlatformContent.external_id == "active_content_1")
    )
    assert check_active is not None

    # Verify expired memory is soft-deleted
    await db_session.refresh(expired_memory)
    assert expired_memory.deleted_at is not None


@pytest.mark.asyncio
async def test_scheduler_expire_stale_recommendations(
    db_session: AsyncSession, test_user: User
) -> None:
    service = SchedulerService()
    past_time = datetime.now(UTC) - timedelta(hours=2)

    stale_rec = Recommendation(
        user_id=test_user.id,
        action_type=ActionType.ORIGINAL_POST.value,
        status=RecommendationStatus.AWAITING_REVIEW.value,
        title="Time Sensitive Post",
        purpose="React to today's news",
        target_audience="General Audience",
        why_now="Timely topic",
        expires_at=past_time,
    )
    db_session.add(stale_rec)
    await db_session.commit()

    count = await service.expire_stale_recommendations(db_session)
    assert count >= 1

    await db_session.refresh(stale_rec)
    assert stale_rec.status == RecommendationStatus.EXPIRED.value


@pytest.mark.asyncio
async def test_scheduler_trigger_due_measurements(
    db_session: AsyncSession, test_user: User
) -> None:
    service = SchedulerService()
    past_time = datetime.now(UTC) - timedelta(hours=1)

    rec = Recommendation(
        user_id=test_user.id,
        action_type=ActionType.COMMENT.value,
        status=RecommendationStatus.REPORTED_PERFORMED.value,
        title="Comment on Tech Discussion",
        purpose="Add value to OSS thread",
        target_audience="Engineers",
        why_now="Recent discussion",
    )
    db_session.add(rec)
    await db_session.commit()

    action = ActionRecord(
        user_id=test_user.id,
        recommendation_id=rec.id,
        status=RecommendationStatus.REPORTED_PERFORMED.value,
        performed_at=datetime.now(UTC) - timedelta(hours=25),
        measurement_due_at=past_time,
    )
    db_session.add(action)
    await db_session.commit()

    count = await service.trigger_due_measurements(db_session)
    assert count >= 1

    await db_session.refresh(action)
    await db_session.refresh(rec)
    assert action.status == RecommendationStatus.MEASUREMENT_SCHEDULED.value
    assert rec.status == RecommendationStatus.MEASUREMENT_SCHEDULED.value


@pytest.mark.asyncio
async def test_scheduler_check_connector_health(db_session: AsyncSession, test_user: User) -> None:
    service = SchedulerService()
    past_time = datetime.now(UTC) - timedelta(minutes=15)

    expired_account = ConnectorAccount(
        user_id=test_user.id,
        platform=Platform.X.value,
        status=ConnectorStatus.CONNECTED.value,
        token_expires_at=past_time,
        encrypted_access_token="test_token",
    )
    db_session.add(expired_account)
    await db_session.commit()

    count = await service.check_connector_health(db_session)
    assert count >= 1

    await db_session.refresh(expired_account)
    assert expired_account.status == ConnectorStatus.EXPIRED.value


@pytest.mark.asyncio
async def test_scheduler_run_all_due_jobs(db_session: AsyncSession, test_user: User) -> None:
    service = SchedulerService()
    summary = await service.run_all_due_jobs(db_session)
    assert "timestamp" in summary
    assert "retention" in summary
    assert "expired_recommendations" in summary
    assert "scheduled_measurements" in summary
    assert "expired_connectors" in summary


@pytest.mark.asyncio
async def test_async_scheduler_lifecycle() -> None:
    scheduler = AsyncScheduler()
    # Test run_once
    result = await scheduler.run_once()
    assert result is not None
    assert scheduler.last_run_at is not None

    # Test start and stop
    await scheduler.start()
    assert scheduler.is_running is False  # Because scheduler_enabled is False in test settings
    await scheduler.stop()
