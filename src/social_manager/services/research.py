from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.schemas import EcosystemAnalysis
from social_manager.config import Settings, get_settings
from social_manager.db.models import ResearchItem, ResearchPacket


class ResearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def create_packet(
        self,
        session: AsyncSession,
        user_id: str,
        analysis: EcosystemAnalysis,
        *,
        goal_id: str | None = None,
        source_count: int = 0,
    ) -> ResearchPacket:
        now = datetime.now(UTC)
        packet = ResearchPacket(
            user_id=user_id,
            goal_id=goal_id,
            title=f"Ecosystem research {now.date().isoformat()}",
            summary=analysis.summary,
            coverage_notes=analysis.coverage_notes,
            source_count=source_count,
            freshness_checked_at=now,
            expires_at=now + timedelta(hours=self.settings.default_research_retention_hours),
            packet_metadata={"finding_count": len(analysis.findings)},
        )
        session.add(packet)
        await session.flush()
        for finding in analysis.findings:
            session.add(
                ResearchItem(
                    packet_id=packet.id,
                    user_id=user_id,
                    kind=finding.kind,
                    title=finding.title,
                    description=finding.description,
                    source_content_ids=finding.source_content_ids,
                    source_urls=finding.source_urls,
                    audience_relevance=finding.audience_relevance,
                    confidence=finding.confidence,
                    recommended_stance=finding.recommended_stance,
                    expires_at=packet.expires_at,
                    item_metadata=finding.metadata,
                )
            )
        await session.commit()
        await session.refresh(packet)
        return packet

    async def latest_packet(
        self, session: AsyncSession, user_id: str
    ) -> tuple[ResearchPacket | None, list[ResearchItem]]:
        now = datetime.now(UTC)
        packet = await session.scalar(
            select(ResearchPacket)
            .where(
                ResearchPacket.user_id == user_id,
                ResearchPacket.expires_at > now,
            )
            .order_by(ResearchPacket.created_at.desc())
        )
        if packet is None:
            return None, []
        result = await session.scalars(
            select(ResearchItem)
            .where(ResearchItem.packet_id == packet.id)
            .order_by(ResearchItem.audience_relevance.desc(), ResearchItem.confidence.desc())
        )
        return packet, list(result)
