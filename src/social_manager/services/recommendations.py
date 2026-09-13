from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.schemas import RecommendationCandidate
from social_manager.db.models import (
    ActionRecord,
    MetricSnapshot,
    Recommendation,
    ReviewFeedback,
)
from social_manager.domain.enums import RecommendationStatus, ReviewDecision
from social_manager.domain.schemas import ActionPerformedInput, MetricsInput, ReviewInput
from social_manager.services.events import EventService


class RecommendationNotFoundError(ValueError):
    pass


class InvalidRecommendationTransition(ValueError):
    pass


class RecommendationService:
    def __init__(self, event_service: EventService | None = None) -> None:
        self.events = event_service or EventService()

    async def create_many(
        self,
        session: AsyncSession,
        user_id: str,
        candidates: list[RecommendationCandidate],
        *,
        workflow_run_id: str | None = None,
        strategy_version_id: str | None = None,
        hypothesis_id: str | None = None,
    ) -> list[Recommendation]:
        records: list[Recommendation] = []
        for candidate in candidates:
            record = Recommendation(
                user_id=user_id,
                workflow_run_id=workflow_run_id,
                strategy_version_id=strategy_version_id,
                hypothesis_id=hypothesis_id,
                action_type=candidate.action_type.value,
                platform=candidate.platform.value if candidate.platform else None,
                status=RecommendationStatus.AWAITING_REVIEW.value,
                title=candidate.title,
                purpose=candidate.purpose,
                target_audience=candidate.target_audience,
                why_now=candidate.why_now,
                draft=candidate.draft,
                effort_minutes=candidate.effort_minutes,
                score=candidate.score,
                evidence_ids=candidate.evidence_ids,
                source_urls=candidate.source_urls,
                risks=candidate.risks,
                unknowns=candidate.unknowns,
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
            session.add(record)
            records.append(record)
        await session.flush()
        for record in records:
            await self.events.emit(
                session,
                event_type="recommendation_ready_for_review",
                aggregate_type="recommendation",
                aggregate_id=record.id,
                user_id=user_id,
                payload={"action_type": record.action_type, "platform": record.platform},
            )
        await session.commit()
        for record in records:
            await session.refresh(record)
        return records

    async def list(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        status: RecommendationStatus | None = None,
        limit: int = 100,
    ) -> list[Recommendation]:
        query = select(Recommendation).where(Recommendation.user_id == user_id)
        if status:
            query = query.where(Recommendation.status == status.value)
        result = await session.scalars(
            query.order_by(Recommendation.created_at.desc()).limit(limit)
        )
        return list(result)

    async def get_owned(
        self, session: AsyncSession, user_id: str, recommendation_id: str
    ) -> Recommendation:
        record = await session.get(Recommendation, recommendation_id)
        if record is None or record.user_id != user_id:
            raise RecommendationNotFoundError("Recommendation not found")
        return record

    async def review(
        self,
        session: AsyncSession,
        user_id: str,
        recommendation_id: str,
        review: ReviewInput,
    ) -> Recommendation:
        recommendation = await self.get_owned(session, user_id, recommendation_id)
        status_by_decision = {
            ReviewDecision.APPROVE: RecommendationStatus.APPROVED,
            ReviewDecision.EDIT: RecommendationStatus.EDITED,
            ReviewDecision.REJECT: RecommendationStatus.REJECTED,
            ReviewDecision.LATER: RecommendationStatus.POSTPONED,
        }
        new_status = status_by_decision[review.decision]
        if recommendation.status != RecommendationStatus.AWAITING_REVIEW.value:
            if recommendation.status in {
                new_status.value,
                RecommendationStatus.REPORTED_PERFORMED.value,
                RecommendationStatus.MEASUREMENT_SCHEDULED.value,
                RecommendationStatus.MEASURED.value,
            }:
                return recommendation
            raise InvalidRecommendationTransition("Recommendation is not awaiting review")

        recommendation.status = new_status.value
        if review.decision == ReviewDecision.APPROVE:
            recommendation.final_text = recommendation.draft
        elif review.decision == ReviewDecision.EDIT:
            recommendation.final_text = review.final_text
        elif review.decision == ReviewDecision.LATER and review.postpone_until:
            recommendation.expires_at = review.postpone_until

        session.add(
            ReviewFeedback(
                user_id=user_id,
                recommendation_id=recommendation.id,
                decision=review.decision.value,
                reason_category=review.reason_category,
                reason_text=review.reason_text,
                scope=review.scope.value,
                original_text=recommendation.draft,
                final_text=recommendation.final_text,
            )
        )
        if review.decision in {ReviewDecision.APPROVE, ReviewDecision.EDIT}:
            existing_action = await session.scalar(
                select(ActionRecord).where(ActionRecord.recommendation_id == recommendation.id)
            )
            if existing_action is None:
                session.add(
                    ActionRecord(
                        user_id=user_id,
                        recommendation_id=recommendation.id,
                        status=new_status.value,
                        action_metadata={"manual_execution_required": True},
                    )
                )
        event_by_decision = {
            ReviewDecision.APPROVE: "recommendation_approved",
            ReviewDecision.EDIT: "recommendation_edited",
            ReviewDecision.REJECT: "recommendation_rejected",
            ReviewDecision.LATER: "recommendation_postponed",
        }
        await self.events.emit(
            session,
            event_type=event_by_decision[review.decision],
            aggregate_type="recommendation",
            aggregate_id=recommendation.id,
            user_id=user_id,
            payload={"feedback_scope": review.scope.value},
        )
        await session.commit()
        await session.refresh(recommendation)
        return recommendation

    async def report_performed(
        self,
        session: AsyncSession,
        user_id: str,
        recommendation_id: str,
        data: ActionPerformedInput,
    ) -> ActionRecord:
        recommendation = await self.get_owned(session, user_id, recommendation_id)
        allowed = {
            RecommendationStatus.APPROVED.value,
            RecommendationStatus.EDITED.value,
            RecommendationStatus.HANDED_OFF.value,
            RecommendationStatus.REPORTED_PERFORMED.value,
        }
        if recommendation.status not in allowed:
            raise InvalidRecommendationTransition(
                "Only an approved, edited, or handed-off recommendation can be performed"
            )
        action = await session.scalar(
            select(ActionRecord).where(ActionRecord.recommendation_id == recommendation.id)
        )
        if action is None:
            action = ActionRecord(
                user_id=user_id,
                recommendation_id=recommendation.id,
                status=RecommendationStatus.APPROVED.value,
            )
            session.add(action)
        performed_at = data.performed_at or datetime.now(UTC)
        action.status = RecommendationStatus.REPORTED_PERFORMED.value
        action.performed_at = performed_at
        action.public_url = data.public_url
        action.external_id = data.external_id
        action.measurement_due_at = performed_at + timedelta(hours=24)
        action.action_metadata = {**action.action_metadata, "notes": data.notes}
        recommendation.status = RecommendationStatus.REPORTED_PERFORMED.value
        await session.flush()
        await self.events.emit(
            session,
            event_type="action_reported_performed",
            aggregate_type="action",
            aggregate_id=action.id,
            user_id=user_id,
            payload={"recommendation_id": recommendation.id},
        )
        await self.events.emit(
            session,
            event_type="measurement_due",
            aggregate_type="action",
            aggregate_id=action.id,
            user_id=user_id,
            payload={"recommendation_id": recommendation.id},
            available_at=action.measurement_due_at,
        )
        await session.commit()
        await session.refresh(action)
        return action

    async def add_metrics(
        self,
        session: AsyncSession,
        user_id: str,
        action_id: str,
        platform: str,
        data: MetricsInput,
    ) -> MetricSnapshot:
        action = await session.get(ActionRecord, action_id)
        if action is None or action.user_id != user_id:
            raise RecommendationNotFoundError("Action not found")
        if action.performed_at is None:
            raise InvalidRecommendationTransition("Metrics require a performed action")
        snapshot = MetricSnapshot(
            action_id=action.id,
            user_id=user_id,
            platform=platform,
            captured_at=data.captured_at or datetime.now(UTC),
            window_hours=data.window_hours,
            metrics=data.metrics,
            visible_participants=data.visible_participants,
            source=data.source,
            completeness=data.completeness,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return snapshot
