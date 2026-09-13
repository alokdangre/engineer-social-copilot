from __future__ import annotations

from typing import Any, TypedDict


class BaseWorkflowState(TypedDict, total=False):
    user_id: str
    workflow_run_id: str
    thread_id: str
    input: dict[str, Any]
    errors: list[str]
    warnings: list[str]
    output: dict[str, Any]


class ProfileState(BaseWorkflowState, total=False):
    source_context: dict[str, Any]
    profile_analysis: dict[str, Any]
    review: dict[str, Any]
    memory_ids: list[str]
    strategy_id: str


class DailyCaptureState(BaseWorkflowState, total=False):
    daily_text: str
    evidence: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]
    daily_analysis: dict[str, Any]
    memory_ids: list[str]


class ResearchState(BaseWorkflowState, total=False):
    research_context: dict[str, Any]
    ecosystem_analysis: dict[str, Any]
    packet_id: str
    hypothesis_ids: list[str]


class RecommendationState(BaseWorkflowState, total=False):
    recommendation_context: dict[str, Any]
    recommendation_set: dict[str, Any]
    recommendation_ids: list[str]
    review: dict[str, Any]
    reviewed_recommendation_id: str


class OutcomeState(BaseWorkflowState, total=False):
    outcome_context: dict[str, Any]
    outcome_analysis: dict[str, Any]
    outcome_id: str
    proposed_strategy_id: str | None
