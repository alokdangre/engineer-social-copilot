from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import DomainEvent


class EventService:
    async def emit(
        self,
        session: AsyncSession,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        user_id: str | None,
        payload: dict[str, Any] | None = None,
        available_at: datetime | None = None,
    ) -> DomainEvent:
        event = DomainEvent(
            user_id=user_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            status="pending",
            available_at=available_at or datetime.now(UTC),
        )
        session.add(event)
        await session.flush()
        return event
