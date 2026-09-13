from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from social_manager.agent.model_gateway import ModelGateway
from social_manager.agent.schemas import OutcomeAnalysis
from social_manager.agent.state import OutcomeState
from social_manager.db.models import (
    ActionRecord,
    MetricSnapshot,
    OutcomeRecord,
    Recommendation,
)
from social_manager.db.session import database
from social_manager.domain.enums import HypothesisStatus, RecommendationStatus
from social_manager.services.strategy import StrategyService

OUTCOME_SYSTEM_PROMPT = """
Analyze the user's own performed action and available outcomes. Keep missing analytics visible
and compare only genuinely similar actions. Distinguish visible participants from all viewers,
and do not infer friendship, hiring intent, or causality from reactions. One outlier cannot
establish a permanent strategy. Proposed strategy changes must be small, tactical, and supported
by repeated or meaningful evidence; never change career identity or goals automatically. Return
only the requested schema.
""".strip()


def build_outcome_graph(
    model_gateway: ModelGateway | None = None,
    strategy_service: StrategyService | None = None,
) -> StateGraph[OutcomeState]:
    model = model_gateway or ModelGateway()
    strategies = strategy_service or StrategyService()

    async def load_outcome_context(state: OutcomeState) -> dict[str, Any]:
        action_id = state.get("input", {}).get("action_id")
        async with database.session_factory() as session:
            query = select(ActionRecord).where(ActionRecord.user_id == state["user_id"])
            if action_id:
                query = query.where(ActionRecord.id == str(action_id))
            else:
                query = query.where(ActionRecord.performed_at.is_not(None)).order_by(
                    ActionRecord.measurement_due_at.asc().nullslast()
                )
            action = await session.scalar(query)
            if action is None:
                raise ValueError("No performed action is available for outcome analysis")
            recommendation = await session.get(Recommendation, action.recommendation_id)
            if recommendation is None:
                raise ValueError("Recommendation for action was not found")
            snapshots = list(
                await session.scalars(
                    select(MetricSnapshot)
                    .where(MetricSnapshot.action_id == action.id)
                    .order_by(MetricSnapshot.captured_at.asc())
                )
            )
            comparable_recommendations = list(
                await session.scalars(
                    select(Recommendation)
                    .where(
                        Recommendation.user_id == state["user_id"],
                        Recommendation.id != recommendation.id,
                        Recommendation.action_type == recommendation.action_type,
                        Recommendation.platform == recommendation.platform,
                        Recommendation.status == RecommendationStatus.MEASURED.value,
                    )
                    .order_by(Recommendation.created_at.desc())
                    .limit(10)
                )
            )
        context = {
            "action": {
                "id": action.id,
                "status": action.status,
                "performed_at": action.performed_at.isoformat() if action.performed_at else None,
                "public_url": action.public_url,
                "metadata": action.action_metadata,
            },
            "recommendation": {
                "id": recommendation.id,
                "action_type": recommendation.action_type,
                "platform": recommendation.platform,
                "title": recommendation.title,
                "purpose": recommendation.purpose,
                "target_audience": recommendation.target_audience,
                "draft": recommendation.draft,
                "final_text": recommendation.final_text,
                "hypothesis_id": recommendation.hypothesis_id,
                "strategy_version_id": recommendation.strategy_version_id,
            },
            "metrics": [
                {
                    "captured_at": item.captured_at.isoformat(),
                    "window_hours": item.window_hours,
                    "metrics": item.metrics,
                    "visible_participants": item.visible_participants,
                    "source": item.source,
                    "completeness": item.completeness,
                }
                for item in snapshots
            ],
            "user_reported_outcomes": state.get("input", {}).get("qualitative_outcomes", {}),
            "comparable_actions": [
                {
                    "id": item.id,
                    "title": item.title,
                    "score": item.score,
                    "created_at": item.created_at.isoformat(),
                }
                for item in comparable_recommendations
            ],
        }
        return {"outcome_context": context}

    async def analyze_outcome(state: OutcomeState) -> dict[str, Any]:
        context = state["outcome_context"]
        fallback = _fallback_outcome(context)
        analysis = await model.generate(
            OutcomeAnalysis,
            system_prompt=OUTCOME_SYSTEM_PROMPT,
            payload={"outcome_context": context},
            fallback=fallback,
        )
        return {"outcome_analysis": analysis.model_dump(mode="json")}

    async def persist_outcome(state: OutcomeState) -> dict[str, Any]:
        analysis = OutcomeAnalysis.model_validate(state["outcome_analysis"])
        context = state["outcome_context"]
        action_id = context["action"]["id"]
        recommendation_id = context["recommendation"]["id"]
        hypothesis_id = context["recommendation"].get("hypothesis_id")
        async with database.session_factory() as session:
            outcome = OutcomeRecord(
                action_id=action_id,
                user_id=state["user_id"],
                summary=analysis.summary,
                audience_fit=analysis.audience_fit,
                relationship_outcome=analysis.relationship_outcome,
                career_outcome=analysis.career_outcome,
                baseline_comparison=analysis.baseline_comparison,
                hypothesis_result=analysis.hypothesis_result,
                uncertainty=analysis.uncertainty,
                evidence=analysis.evidence,
            )
            session.add(outcome)
            action = await session.get(ActionRecord, action_id)
            recommendation = await session.get(Recommendation, recommendation_id)
            if action:
                action.status = RecommendationStatus.MEASURED.value
            if recommendation:
                recommendation.status = RecommendationStatus.MEASURED.value
            if hypothesis_id:
                await strategies.apply_hypothesis_result(
                    session,
                    state["user_id"],
                    hypothesis_id,
                    analysis.hypothesis_result,
                    {
                        "action_id": action_id,
                        "summary": analysis.summary,
                        "uncertainty": analysis.uncertainty,
                    },
                )
            await session.commit()
            await session.refresh(outcome)
            proposed_strategy = None
            if analysis.proposed_strategy_changes:
                proposed_strategy = await strategies.next_version(
                    session,
                    state["user_id"],
                    proposed_changes=analysis.proposed_strategy_changes,
                    rationale=f"Proposed from outcome {outcome.id}; requires strategy review",
                )
        return {
            "outcome_id": outcome.id,
            "proposed_strategy_id": proposed_strategy.id if proposed_strategy else None,
            "output": {
                "outcome_id": outcome.id,
                "summary": analysis.summary,
                "hypothesis_result": analysis.hypothesis_result,
                "uncertainty": analysis.uncertainty,
                "proposed_strategy_id": proposed_strategy.id if proposed_strategy else None,
            },
        }

    builder = StateGraph(OutcomeState)
    builder.add_node("load_outcome_context", load_outcome_context)
    builder.add_node("analyze_outcome", analyze_outcome)
    builder.add_node("persist_outcome", persist_outcome)
    builder.add_edge(START, "load_outcome_context")
    builder.add_edge("load_outcome_context", "analyze_outcome")
    builder.add_edge("analyze_outcome", "persist_outcome")
    builder.add_edge("persist_outcome", END)
    return builder


def _fallback_outcome(context: dict[str, Any]) -> OutcomeAnalysis:
    snapshots = context.get("metrics", [])
    qualitative = context.get("user_reported_outcomes", {})
    latest = snapshots[-1] if snapshots else None
    metrics = latest.get("metrics", {}) if latest else {}
    visible = latest.get("visible_participants", []) if latest else []
    uncertainty: list[str] = []
    if not latest:
        uncertainty.append("No quantitative analytics are available")
    elif latest.get("completeness") != "complete":
        uncertainty.append("The latest metric snapshot is incomplete")
    if not context.get("comparable_actions"):
        uncertainty.append("No comparable measured actions are available")
    metric_summary = ", ".join(f"{key}={value}" for key, value in metrics.items())
    summary = (
        f"Observed metrics: {metric_summary}."
        if metric_summary
        else "No quantitative result observed."
    )
    if qualitative:
        summary += " User-reported qualitative outcomes were supplied."
    audience_fit = (
        f"{len(visible)} visible participants were supplied; they do not represent all viewers."
        if visible
        else "Audience fit is unknown because no visible participant evidence was supplied."
    )
    rel_outcome = qualitative.get("relationship") if qualitative else None
    career_outcome = qualitative.get("career") if qualitative else None
    return OutcomeAnalysis(
        summary=summary,
        audience_fit=audience_fit,
        relationship_outcome=str(rel_outcome) if rel_outcome else None,
        career_outcome=str(career_outcome) if career_outcome else None,
        baseline_comparison=(
            "Comparable historical actions require direct outcome records before a reliable "
            "comparison."
        ),
        hypothesis_result=HypothesisStatus.INCONCLUSIVE.value,
        uncertainty=uncertainty,
        evidence=[{"source": latest.get("source"), "metrics": metrics}] if latest else [],
        proposed_strategy_changes=[],
    )


outcome_strategy_graph = build_outcome_graph().compile()
