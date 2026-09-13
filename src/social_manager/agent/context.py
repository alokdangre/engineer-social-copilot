from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import Goal, PlatformContent, User


async def load_user_context(session: AsyncSession, user_id: str) -> dict[str, Any]:
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise ValueError("User not found")
    goals = list(
        await session.scalars(
            select(Goal)
            .where(Goal.user_id == user_id, Goal.status == "active")
            .order_by(Goal.priority.desc())
        )
    )
    now = datetime.now(UTC)
    content = list(
        await session.scalars(
            select(PlatformContent)
            .where(
                PlatformContent.user_id == user_id,
                or_(
                    PlatformContent.retention_expires_at.is_(None),
                    PlatformContent.retention_expires_at > now,
                ),
            )
            .order_by(PlatformContent.published_at.desc().nullslast())
            .limit(100)
        )
    )
    return {
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "timezone": user.timezone,
        },
        "goals": [
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "target_audiences": goal.target_audiences,
                "success_criteria": goal.success_criteria,
                "priority": goal.priority,
            }
            for goal in goals
        ],
        "content": [serialize_content(item) for item in content],
    }


def serialize_content(item: PlatformContent) -> dict[str, Any]:
    return {
        "id": item.id,
        "platform": item.platform,
        "external_id": item.external_id,
        "content_type": item.content_type,
        "author_name": item.author_name,
        "body": item.body,
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "metrics": item.metrics,
        "normalized_data": item.normalized_data,
        "is_own": item.is_own,
        "access_method": item.access_method,
    }
