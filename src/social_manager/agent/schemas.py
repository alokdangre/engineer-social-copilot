from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from social_manager.domain.enums import (
    ActionType,
    EvidenceStatus,
    MemoryCategory,
    Platform,
    Sensitivity,
    Visibility,
)


class MemoryCandidate(BaseModel):
    category: MemoryCategory
    title: str
    statement: str
    evidence_status: EvidenceStatus
    confidence: float = Field(ge=0, le=1)
    visibility: Visibility
    sensitivity: Sensitivity = Sensitivity.NONE
    source_platform: Platform = Platform.USER
    source_reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProfileAnalysis(BaseModel):
    software_journey: list[str] = Field(default_factory=list)
    credible_skills: list[MemoryCandidate] = Field(default_factory=list)
    projects: list[MemoryCandidate] = Field(default_factory=list)
    voice_observations: list[MemoryCandidate] = Field(default_factory=list)
    positioning: str
    content_pillars: list[str] = Field(default_factory=list)
    inconsistencies: list[str] = Field(default_factory=list)
    confirmation_questions: list[str] = Field(default_factory=list)


class DailyAnalysis(BaseModel):
    facts: list[MemoryCandidate] = Field(default_factory=list)
    opinions: list[MemoryCandidate] = Field(default_factory=list)
    questions: list[MemoryCandidate] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    content_angles: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class ResearchFinding(BaseModel):
    kind: str
    title: str
    description: str
    source_content_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    audience_relevance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    recommended_stance: str = "observe"
    metadata: dict[str, Any] = Field(default_factory=dict)


class HypothesisCandidate(BaseModel):
    statement: str
    observation: str
    platform: Platform | None = None
    target_audience: str
    expected_outcome: str
    confidence: float = Field(default=0.3, ge=0, le=1)
    success_criteria: list[str] = Field(default_factory=list)
    measurement_window_hours: int = 168


class EcosystemAnalysis(BaseModel):
    summary: str
    coverage_notes: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    hypotheses: list[HypothesisCandidate] = Field(default_factory=list)


class RecommendationCandidate(BaseModel):
    action_type: ActionType
    platform: Platform | None = None
    title: str
    purpose: str
    target_audience: str
    why_now: str
    draft: str | None = None
    effort_minutes: int = Field(default=10, ge=0, le=1440)
    score: float = Field(default=0.5, ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class RecommendationSet(BaseModel):
    recommendations: list[RecommendationCandidate] = Field(default_factory=list)
    excluded_candidates: list[dict[str, str]] = Field(default_factory=list)


class OutcomeAnalysis(BaseModel):
    summary: str
    audience_fit: str
    relationship_outcome: str | None = None
    career_outcome: str | None = None
    baseline_comparison: str
    hypothesis_result: str = "inconclusive"
    uncertainty: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    proposed_strategy_changes: list[str] = Field(default_factory=list)
