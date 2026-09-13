from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.config import Settings, get_settings
from social_manager.db.models import (
    ActionRecord,
    ConnectorAccount,
    MemoryRecord,
    PlatformContent,
    Recommendation,
)
from social_manager.db.session import database
from social_manager.domain.enums import ConnectorStatus, RecommendationStatus
from social_manager.services.events import EventService

logger = structlog.get_logger(__name__)


class SchedulerService:
    """Core domain scheduler tasks for retention, expiration, and measurement lifecycle."""

    def __init__(
        self,
        event_service: EventService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.events = event_service or EventService()
        self.settings = settings or get_settings()

    async def purge_expired_retention(
        self, session: AsyncSession, now: datetime | None = None
    ) -> dict[str, int]:
        """Purges or soft-deletes records whose retention period has expired."""
        current_time = now or datetime.now(UTC)

        # 1. Platform Content
        content_stmt = select(PlatformContent).where(
            and_(
                PlatformContent.retention_expires_at.is_not(None),
                PlatformContent.retention_expires_at <= current_time,
            )
        )
        expired_content = list((await session.scalars(content_stmt)).all())
        content_count = len(expired_content)
        for item in expired_content:
            await session.delete(item)

        # 2. Memories past retention
        memories_stmt = select(MemoryRecord).where(
            and_(
                MemoryRecord.deleted_at.is_(None),
                MemoryRecord.retention_expires_at.is_not(None),
                MemoryRecord.retention_expires_at <= current_time,
            )
        )
        expired_memories = list((await session.scalars(memories_stmt)).all())
        memory_count = len(expired_memories)
        for mem in expired_memories:
            mem.deleted_at = current_time

        await session.commit()
        logger.info(
            "retention_cleanup_completed",
            purged_content=content_count,
            purged_memories=memory_count,
        )
        return {"purged_content": content_count, "purged_memories": memory_count}

    async def expire_stale_recommendations(
        self, session: AsyncSession, now: datetime | None = None
    ) -> int:
        """Marks awaiting_review recommendations as expired once their expires_at has passed."""
        current_time = now or datetime.now(UTC)
        stmt = select(Recommendation).where(
            and_(
                Recommendation.status.in_(
                    [
                        RecommendationStatus.AWAITING_REVIEW.value,
                        RecommendationStatus.DRAFT.value,
                    ]
                ),
                Recommendation.expires_at.is_not(None),
                Recommendation.expires_at <= current_time,
            )
        )
        stale_recs = list((await session.scalars(stmt)).all())
        expired_count = len(stale_recs)

        for rec in stale_recs:
            rec.status = RecommendationStatus.EXPIRED.value
            await self.events.emit(
                session,
                event_type="recommendation_expired",
                aggregate_type="recommendation",
                aggregate_id=rec.id,
                user_id=rec.user_id,
                payload={"action_type": rec.action_type, "platform": rec.platform},
            )

        await session.commit()
        logger.info("stale_recommendations_expired", expired_count=expired_count)
        return expired_count

    async def trigger_due_measurements(
        self, session: AsyncSession, now: datetime | None = None
    ) -> int:
        """Detects performed actions whose measurement window is due and updates their status."""
        current_time = now or datetime.now(UTC)
        stmt = select(ActionRecord).where(
            and_(
                ActionRecord.status.in_(
                    [
                        RecommendationStatus.REPORTED_PERFORMED.value,
                        RecommendationStatus.VERIFIED_PERFORMED.value,
                    ]
                ),
                ActionRecord.measurement_due_at.is_not(None),
                ActionRecord.measurement_due_at <= current_time,
            )
        )
        due_actions = list((await session.scalars(stmt)).all())
        scheduled_count = len(due_actions)

        for action in due_actions:
            action.status = RecommendationStatus.MEASUREMENT_SCHEDULED.value
            # Synchronize linked recommendation status if present
            if action.recommendation_id:
                rec = await session.get(Recommendation, action.recommendation_id)
                if rec and rec.status in {
                    RecommendationStatus.REPORTED_PERFORMED.value,
                    RecommendationStatus.VERIFIED_PERFORMED.value,
                }:
                    rec.status = RecommendationStatus.MEASUREMENT_SCHEDULED.value

            await self.events.emit(
                session,
                event_type="measurement_due",
                aggregate_type="action",
                aggregate_id=action.id,
                user_id=action.user_id,
                payload={
                    "recommendation_id": action.recommendation_id,
                    "performed_at": (
                        action.performed_at.isoformat() if action.performed_at else None
                    ),
                },
            )

        await session.commit()
        logger.info("due_measurements_triggered", scheduled_count=scheduled_count)
        return scheduled_count

    async def check_connector_health(
        self, session: AsyncSession, now: datetime | None = None
    ) -> int:
        """Checks for expired OAuth credentials and marks accounts accordingly."""
        current_time = now or datetime.now(UTC)
        stmt = select(ConnectorAccount).where(
            and_(
                ConnectorAccount.status == ConnectorStatus.CONNECTED.value,
                ConnectorAccount.token_expires_at.is_not(None),
                ConnectorAccount.token_expires_at <= current_time,
            )
        )
        expired_accounts = list((await session.scalars(stmt)).all())
        count = len(expired_accounts)

        for account in expired_accounts:
            account.status = ConnectorStatus.EXPIRED.value
            account.last_error = "OAuth access token expired"

        await session.commit()
        logger.info("connector_health_checked", expired_tokens=count)
        return count

    async def run_all_due_jobs(
        self, session: AsyncSession, now: datetime | None = None
    ) -> dict[str, Any]:
        """Executes all scheduled maintenance and lifecycle jobs."""
        retention = await self.purge_expired_retention(session, now=now)
        expired_recs = await self.expire_stale_recommendations(session, now=now)
        scheduled_measurements = await self.trigger_due_measurements(session, now=now)
        expired_connectors = await self.check_connector_health(session, now=now)
        return {
            "timestamp": (now or datetime.now(UTC)).isoformat(),
            "retention": retention,
            "expired_recommendations": expired_recs,
            "scheduled_measurements": scheduled_measurements,
            "expired_connectors": expired_connectors,
        }


class AsyncScheduler:
    """In-process periodic background task scheduler for local, staging, and container runs."""

    def __init__(
        self,
        service: SchedulerService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.service = service or SchedulerService()
        self.settings = settings or get_settings()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self.last_run_at: datetime | None = None
        self.last_run_result: dict[str, Any] | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if not self.settings.scheduler_enabled:
            logger.info("scheduler_disabled_by_config")
            return
        if self.is_running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="social-media-scheduler")
        logger.info(
            "scheduler_started",
            interval_seconds=self.settings.scheduler_interval_seconds,
        )

    async def stop(self) -> None:
        if not self.is_running or self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("scheduler_stopped")

    async def run_once(self) -> dict[str, Any]:
        async with database.session_factory() as session:
            result = await self.service.run_all_due_jobs(session)
            self.last_run_at = datetime.now(UTC)
            self.last_run_result = result
            return result

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception:
                logger.exception("scheduler_job_execution_failed")
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=float(self.settings.scheduler_interval_seconds),
                )
            except TimeoutError:
                continue


app_scheduler = AsyncScheduler()
