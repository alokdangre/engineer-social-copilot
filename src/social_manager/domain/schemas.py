from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from social_manager.domain.enums import (
    ActionType,
    ConnectorStatus,
    ContentType,
    EvidenceStatus,
    FeedbackScope,
    HypothesisStatus,
    LLMProvider,
    MemoryCategory,
    Platform,
    RecommendationStatus,
    ReviewDecision,
    Sensitivity,
    SourceAccessMethod,
    Visibility,
    WorkflowKind,
    WorkflowStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    display_name: str = Field(min_length=1, max_length=160)
    timezone: str = Field(default="UTC", max_length=80)


class UserRead(ORMModel):
    id: str
    email: EmailStr
    display_name: str
    timezone: str
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    timezone: str | None = Field(default=None, max_length=80)


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LLMCredentialInput(BaseModel):
    provider: LLMProvider
    api_key: SecretStr = Field(min_length=10, max_length=4096)


class LLMCredentialRead(BaseModel):
    configured: bool
    provider: LLMProvider | None = None
    key_hint: str | None = None
    updated_at: datetime | None = None


class ConnectorRead(ORMModel):
    id: str
    platform: Platform
    status: ConnectorStatus
    external_user_id: str | None
    username: str | None
    scopes: list[str]
    token_expires_at: datetime | None
    last_sync_at: datetime | None
    last_error: str | None


class ConnectorAuthorization(BaseModel):
    platform: Platform
    authorization_url: str
    expires_at: datetime


class ConnectorTokenInput(BaseModel):
    access_token: str = Field(min_length=1)
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list)


class ConnectorSyncResult(BaseModel):
    platform: Platform
    fetched: int
    created: int
    updated: int
    cursor: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PlatformContentCreate(BaseModel):
    platform: Platform
    external_id: str = Field(min_length=1, max_length=512)
    content_type: ContentType
    author_external_id: str | None = None
    author_name: str | None = None
    body: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    normalized_data: dict[str, Any] = Field(default_factory=dict)
    is_own: bool = False
    access_method: SourceAccessMethod = SourceAccessMethod.USER_PROVIDED
    retention_expires_at: datetime | None = None


class PlatformContentRead(ORMModel):
    id: str
    platform: Platform
    external_id: str
    content_type: ContentType
    author_external_id: str | None
    author_name: str | None
    body: str | None
    url: str | None
    published_at: datetime | None
    metrics: dict[str, Any]
    normalized_data: dict[str, Any]
    is_own: bool
    access_method: SourceAccessMethod
    collected_at: datetime
    retention_expires_at: datetime | None


class MemoryCreate(BaseModel):
    category: MemoryCategory
    title: str = Field(min_length=1, max_length=300)
    statement: str = Field(min_length=1)
    evidence_status: EvidenceStatus
    confidence: float = Field(default=0.5, ge=0, le=1)
    visibility: Visibility = Visibility.PRIVATE
    sensitivity: Sensitivity = Sensitivity.NONE
    source_platform: Platform = Platform.USER
    source_reference: str | None = None
    source_content_id: str | None = None
    observed_at: datetime | None = None
    valid_until: datetime | None = None
    retention_expires_at: datetime | None = None
    usage_rules: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    supersedes_id: str | None = None


class MemoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    statement: str | None = Field(default=None, min_length=1)
    evidence_status: EvidenceStatus | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    visibility: Visibility | None = None
    sensitivity: Sensitivity | None = None
    valid_until: datetime | None = None
    usage_rules: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class MemoryRead(ORMModel):
    id: str
    category: MemoryCategory
    title: str
    statement: str
    evidence_status: EvidenceStatus
    confidence: float
    visibility: Visibility
    sensitivity: Sensitivity
    source_platform: Platform
    source_reference: str | None
    source_content_id: str | None
    observed_at: datetime | None
    captured_at: datetime
    valid_until: datetime | None
    retention_expires_at: datetime | None
    usage_rules: dict[str, Any]
    record_metadata: dict[str, Any]
    supersedes_id: str | None


class MemoryLinkCreate(BaseModel):
    from_record_id: str
    to_record_id: str
    relation: str = Field(min_length=1, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryLinkRead(ORMModel):
    id: str
    from_record_id: str
    to_record_id: str
    relation: str
    link_metadata: dict[str, Any]


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1)
    target_audiences: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    priority: int = Field(default=50, ge=0, le=100)
    target_date: datetime | None = None


class GoalRead(ORMModel):
    id: str
    title: str
    description: str
    target_audiences: list[str]
    success_criteria: list[str]
    priority: int
    status: str
    target_date: datetime | None


class ReviewInput(BaseModel):
    decision: ReviewDecision
    recommendation_id: str | None = None
    final_text: str | None = None
    reason_category: str | None = None
    reason_text: str | None = None
    scope: FeedbackScope = FeedbackScope.THIS_ONLY
    postpone_until: datetime | None = None
    corrections: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_text_for_edit(self) -> ReviewInput:
        if self.decision == ReviewDecision.EDIT and not self.final_text:
            raise ValueError("final_text is required when decision is edit")
        return self


class RecommendationRead(ORMModel):
    id: str
    action_type: ActionType
    platform: Platform | None
    status: RecommendationStatus
    title: str
    purpose: str
    target_audience: str
    why_now: str
    draft: str | None
    final_text: str | None
    effort_minutes: int
    score: float
    evidence_ids: list[str]
    source_urls: list[str]
    risks: list[str]
    unknowns: list[str]
    expires_at: datetime | None
    created_at: datetime


class ActionPerformedInput(BaseModel):
    performed_at: datetime | None = None
    public_url: str | None = None
    external_id: str | None = None
    notes: str | None = None


class ActionRead(ORMModel):
    id: str
    recommendation_id: str
    status: RecommendationStatus
    performed_at: datetime | None
    verified_at: datetime | None
    public_url: str | None
    external_id: str | None
    verification_source: str | None
    measurement_due_at: datetime | None
    action_metadata: dict[str, Any]


class MetricsInput(BaseModel):
    captured_at: datetime | None = None
    window_hours: int | None = Field(default=None, ge=0)
    metrics: dict[str, float | int | None] = Field(default_factory=dict)
    visible_participants: list[dict[str, Any]] = Field(default_factory=list)
    source: str = "user_reported"
    completeness: str = "partial"


class WorkflowStart(BaseModel):
    kind: WorkflowKind
    input: dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None


class WorkflowResume(BaseModel):
    review: ReviewInput | None = None
    value: dict[str, Any] | str | bool | None = None

    @model_validator(mode="after")
    def select_one_resume_value(self) -> WorkflowResume:
        if self.review is None and self.value is None:
            raise ValueError("review or value is required")
        if self.review is not None and self.value is not None:
            raise ValueError("provide review or value, not both")
        return self


class WorkflowRunRead(ORMModel):
    id: str
    kind: WorkflowKind
    thread_id: str
    status: WorkflowStatus
    current_node: str | None
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    interrupt_data: dict[str, Any]
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class WorkflowInvocationResult(BaseModel):
    run: WorkflowRunRead
    recommendations: list[RecommendationRead] = Field(default_factory=list)


class StrategyRead(ORMModel):
    id: str
    version: int
    status: str
    positioning: str
    content_pillars: list[str]
    audience_priorities: list[str]
    platform_tactics: dict[str, Any]
    relationship_approach: str
    excluded_tactics: list[str]
    rationale: str
    previous_version_id: str | None
    activated_at: datetime | None


class HypothesisRead(ORMModel):
    id: str
    statement: str
    observation: str
    platform: Platform | None
    target_audience: str
    expected_outcome: str
    status: HypothesisStatus
    confidence: float
    evidence: list[dict[str, Any]]
    success_criteria: list[str]
    measurement_window_hours: int
