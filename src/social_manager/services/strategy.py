from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.schemas import HypothesisCandidate
from social_manager.db.models import Hypothesis, StrategyVersion
from social_manager.domain.enums import HypothesisStatus


class StrategyService:
    async def current(self, session: AsyncSession, user_id: str) -> StrategyVersion | None:
        result = await session.scalars(
            select(StrategyVersion)
            .where(
                StrategyVersion.user_id == user_id,
                StrategyVersion.status == "active",
            )
            .order_by(StrategyVersion.version.desc())
        )
        return result.first()

    async def ensure_initial(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        positioning: str,
        content_pillars: list[str],
        audience_priorities: list[str],
        rationale: str,
    ) -> StrategyVersion:
        current = await self.current(session, user_id)
        if current is not None:
            return current
        strategy = StrategyVersion(
            user_id=user_id,
            version=1,
            status="active",
            positioning=positioning,
            content_pillars=content_pillars,
            audience_priorities=audience_priorities,
            platform_tactics={
                "github": "evidence and technical work",
                "x": "timely technical conversations and concise insights",
                "linkedin": "professional narrative and deeper career-relevant explanations",
            },
            relationship_approach="Consistent useful participation with genuine context",
            excluded_tactics=[
                "fabricated experience",
                "mass outreach",
                "engagement farming",
                "automatic social actions",
            ],
            rationale=rationale,
            activated_at=datetime.now(UTC),
        )
        session.add(strategy)
        await session.commit()
        await session.refresh(strategy)
        return strategy

    async def create_hypotheses(
        self,
        session: AsyncSession,
        user_id: str,
        candidates: list[HypothesisCandidate],
        strategy_version_id: str | None,
    ) -> list[Hypothesis]:
        hypotheses: list[Hypothesis] = []
        for candidate in candidates:
            hypothesis = Hypothesis(
                user_id=user_id,
                strategy_version_id=strategy_version_id,
                statement=candidate.statement,
                observation=candidate.observation,
                platform=candidate.platform.value if candidate.platform else None,
                target_audience=candidate.target_audience,
                expected_outcome=candidate.expected_outcome,
                status=HypothesisStatus.PROPOSED.value,
                confidence=candidate.confidence,
                evidence=[],
                success_criteria=candidate.success_criteria,
                measurement_window_hours=candidate.measurement_window_hours,
            )
            session.add(hypothesis)
            hypotheses.append(hypothesis)
        await session.commit()
        for hypothesis in hypotheses:
            await session.refresh(hypothesis)
        return hypotheses

    async def list_hypotheses(
        self, session: AsyncSession, user_id: str, limit: int = 100
    ) -> list[Hypothesis]:
        result = await session.scalars(
            select(Hypothesis)
            .where(Hypothesis.user_id == user_id)
            .order_by(Hypothesis.updated_at.desc())
            .limit(limit)
        )
        return list(result)

    async def apply_hypothesis_result(
        self,
        session: AsyncSession,
        user_id: str,
        hypothesis_id: str,
        result: str,
        evidence: dict[str, object],
    ) -> Hypothesis:
        hypothesis = await session.get(Hypothesis, hypothesis_id)
        if hypothesis is None or hypothesis.user_id != user_id:
            raise ValueError("Hypothesis not found")
        allowed = {status.value for status in HypothesisStatus}
        normalized = result if result in allowed else HypothesisStatus.INCONCLUSIVE.value
        hypothesis.status = normalized
        hypothesis.evidence = [*hypothesis.evidence, evidence]
        if normalized == HypothesisStatus.SUPPORTED.value:
            hypothesis.confidence = min(1.0, hypothesis.confidence + 0.15)
        elif normalized in {
            HypothesisStatus.WEAKENED.value,
            HypothesisStatus.CONTRADICTED.value,
        }:
            hypothesis.confidence = max(0.0, hypothesis.confidence - 0.15)
        await session.flush()
        return hypothesis

    async def next_version(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        proposed_changes: list[str],
        rationale: str,
    ) -> StrategyVersion:
        current = await self.current(session, user_id)
        max_version = await session.scalar(
            select(func.max(StrategyVersion.version)).where(StrategyVersion.user_id == user_id)
        )
        strategy = StrategyVersion(
            user_id=user_id,
            version=int(max_version or 0) + 1,
            status="proposed",
            positioning=(
                current.positioning if current else "Technical professional building credibility"
            ),
            content_pillars=current.content_pillars if current else [],
            audience_priorities=current.audience_priorities if current else [],
            platform_tactics={
                **(current.platform_tactics if current else {}),
                "proposed_changes": proposed_changes,
            },
            relationship_approach=current.relationship_approach if current else "",
            excluded_tactics=current.excluded_tactics if current else [],
            rationale=rationale,
            previous_version_id=current.id if current else None,
        )
        session.add(strategy)
        await session.commit()
        await session.refresh(strategy)
        return strategy

    async def activate(
        self, session: AsyncSession, user_id: str, strategy_id: str
    ) -> StrategyVersion:
        strategy = await session.get(StrategyVersion, strategy_id)
        if strategy is None or strategy.user_id != user_id:
            raise ValueError("Strategy version not found")
        current = await self.current(session, user_id)
        if current and current.id != strategy.id:
            current.status = "superseded"
        strategy.status = "active"
        strategy.activated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(strategy)
        return strategy
