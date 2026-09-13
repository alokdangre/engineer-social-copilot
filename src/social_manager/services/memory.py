from __future__ import annotations

import builtins
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.model_gateway import ModelGateway
from social_manager.db.models import MemoryLink, MemoryRecord, PlatformContent
from social_manager.domain.enums import EvidenceStatus, MemoryCategory, Visibility
from social_manager.domain.schemas import MemoryCreate, MemoryLinkCreate, MemoryUpdate


class MemoryNotFoundError(ValueError):
    pass


class MemoryService:
    def __init__(self, model_gateway: ModelGateway | None = None) -> None:
        self.model_gateway = model_gateway or ModelGateway()

    async def create(self, session: AsyncSession, user_id: str, data: MemoryCreate) -> MemoryRecord:
        if data.source_content_id:
            source = await session.get(PlatformContent, data.source_content_id)
            if source is None or source.user_id != user_id:
                raise ValueError("source_content_id does not belong to the user")
        if data.supersedes_id:
            previous = await self.get_owned(session, user_id, data.supersedes_id)
            previous.evidence_status = EvidenceStatus.SUPERSEDED.value

        record = self._build_record(
            user_id,
            data,
            await self.model_gateway.embed(f"{data.title}\n{data.statement}"),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def create_many(
        self, session: AsyncSession, user_id: str, items: list[MemoryCreate]
    ) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        for item in items:
            embedding = await self.model_gateway.embed(f"{item.title}\n{item.statement}")
            record = self._build_record(user_id, item, embedding)
            session.add(record)
            records.append(record)
        await session.commit()
        for record in records:
            await session.refresh(record)
        return records

    @staticmethod
    def _build_record(
        user_id: str, data: MemoryCreate, embedding: list[float] | None
    ) -> MemoryRecord:
        return MemoryRecord(
            user_id=user_id,
            category=data.category.value,
            title=data.title,
            statement=data.statement,
            evidence_status=data.evidence_status.value,
            confidence=data.confidence,
            visibility=data.visibility.value,
            sensitivity=data.sensitivity.value,
            source_platform=data.source_platform.value,
            source_reference=data.source_reference,
            source_content_id=data.source_content_id,
            observed_at=data.observed_at,
            captured_at=datetime.now(UTC),
            valid_until=data.valid_until,
            retention_expires_at=data.retention_expires_at,
            usage_rules=data.usage_rules,
            record_metadata=data.metadata,
            embedding=embedding,
            supersedes_id=data.supersedes_id,
        )

    async def get_owned(self, session: AsyncSession, user_id: str, record_id: str) -> MemoryRecord:
        record = await session.get(MemoryRecord, record_id)
        if record is None or record.user_id != user_id or record.deleted_at is not None:
            raise MemoryNotFoundError("Memory record not found")
        return record

    async def list(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        category: MemoryCategory | None = None,
        visibility: Visibility | None = None,
        query: str | None = None,
        limit: int = 100,
    ) -> builtins.list[MemoryRecord]:
        conditions = [MemoryRecord.user_id == user_id, MemoryRecord.deleted_at.is_(None)]
        now = datetime.now(UTC)
        conditions.append(
            or_(
                MemoryRecord.retention_expires_at.is_(None),
                MemoryRecord.retention_expires_at > now,
            )
        )
        if category:
            conditions.append(MemoryRecord.category == category.value)
        if visibility:
            conditions.append(MemoryRecord.visibility == visibility.value)
        if query:
            pattern = f"%{query.strip()}%"
            conditions.append(
                or_(
                    MemoryRecord.title.ilike(pattern),
                    MemoryRecord.statement.ilike(pattern),
                )
            )
        result = await session.scalars(
            select(MemoryRecord)
            .where(and_(*conditions))
            .order_by(MemoryRecord.updated_at.desc())
            .limit(limit)
        )
        return builtins.list(result)

    async def update(
        self,
        session: AsyncSession,
        user_id: str,
        record_id: str,
        data: MemoryUpdate,
    ) -> MemoryRecord:
        record = await self.get_owned(session, user_id, record_id)
        changes = data.model_dump(exclude_unset=True)
        if "metadata" in changes:
            changes["record_metadata"] = changes.pop("metadata")
        for enum_field in ("evidence_status", "visibility", "sensitivity"):
            if enum_field in changes and changes[enum_field] is not None:
                changes[enum_field] = changes[enum_field].value
        for key, value in changes.items():
            setattr(record, key, value)
        if "title" in changes or "statement" in changes:
            record.embedding = await self.model_gateway.embed(f"{record.title}\n{record.statement}")
        await session.commit()
        await session.refresh(record)
        return record

    async def soft_delete(self, session: AsyncSession, user_id: str, record_id: str) -> None:
        record = await self.get_owned(session, user_id, record_id)
        record.deleted_at = datetime.now(UTC)
        await session.commit()

    async def create_link(
        self, session: AsyncSession, user_id: str, data: MemoryLinkCreate
    ) -> MemoryLink:
        await self.get_owned(session, user_id, data.from_record_id)
        await self.get_owned(session, user_id, data.to_record_id)
        link = MemoryLink(
            user_id=user_id,
            from_record_id=data.from_record_id,
            to_record_id=data.to_record_id,
            relation=data.relation,
            link_metadata=data.metadata,
        )
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

    async def recommendation_packet(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        query: str | None = None,
        limit: int = 30,
    ) -> builtins.list[MemoryRecord]:
        allowed_statuses = [
            EvidenceStatus.OBSERVED.value,
            EvidenceStatus.SELF_REPORTED.value,
            EvidenceStatus.USER_CONFIRMED.value,
            EvidenceStatus.INFERRED.value,
        ]
        allowed_visibility = [
            Visibility.POTENTIALLY_SHAREABLE.value,
            Visibility.APPROVED_PUBLIC.value,
        ]
        conditions = [
            MemoryRecord.user_id == user_id,
            MemoryRecord.deleted_at.is_(None),
            MemoryRecord.evidence_status.in_(allowed_statuses),
            MemoryRecord.visibility.in_(allowed_visibility),
        ]
        if query:
            pattern = f"%{query}%"
            conditions.append(
                or_(
                    MemoryRecord.title.ilike(pattern),
                    MemoryRecord.statement.ilike(pattern),
                )
            )
        result = await session.scalars(
            select(MemoryRecord)
            .where(and_(*conditions))
            .order_by(MemoryRecord.confidence.desc(), MemoryRecord.updated_at.desc())
            .limit(limit)
        )
        return builtins.list(result)
