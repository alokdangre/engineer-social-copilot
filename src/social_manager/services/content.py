from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import PlatformContent
from social_manager.domain.enums import ContentType, Platform
from social_manager.domain.schemas import PlatformContentCreate


class ContentService:
    async def upsert(
        self,
        session: AsyncSession,
        user_id: str,
        data: PlatformContentCreate,
        connector_id: str | None = None,
    ) -> tuple[PlatformContent, bool]:
        content = await session.scalar(
            select(PlatformContent).where(
                PlatformContent.user_id == user_id,
                PlatformContent.platform == data.platform.value,
                PlatformContent.external_id == data.external_id,
            )
        )
        created = content is None
        if content is None:
            content = PlatformContent(
                user_id=user_id,
                connector_id=connector_id,
                platform=data.platform.value,
                external_id=data.external_id,
                content_type=data.content_type.value,
                collected_at=datetime.now(UTC),
                access_method=data.access_method.value,
            )
            session.add(content)
        content.author_external_id = data.author_external_id
        content.author_name = data.author_name
        content.body = data.body
        content.url = data.url
        content.published_at = data.published_at
        content.metrics = data.metrics
        content.normalized_data = data.normalized_data
        content.is_own = data.is_own
        content.access_method = data.access_method.value
        content.retention_expires_at = data.retention_expires_at
        content.collected_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(content)
        return content, created

    async def list(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        platform: Platform | None = None,
        content_type: ContentType | None = None,
        is_own: bool | None = None,
        limit: int = 100,
    ) -> list[PlatformContent]:
        now = datetime.now(UTC)
        conditions = [
            PlatformContent.user_id == user_id,
            or_(
                PlatformContent.retention_expires_at.is_(None),
                PlatformContent.retention_expires_at > now,
            ),
        ]
        if platform:
            conditions.append(PlatformContent.platform == platform.value)
        if content_type:
            conditions.append(PlatformContent.content_type == content_type.value)
        if is_own is not None:
            conditions.append(PlatformContent.is_own == is_own)
        result = await session.scalars(
            select(PlatformContent)
            .where(and_(*conditions))
            .order_by(PlatformContent.published_at.desc().nullslast())
            .limit(limit)
        )
        return list(result)
