from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from social_manager.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from social_manager.db.types import PortableVector


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    connectors: Mapped[list[ConnectorAccount]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OAuthState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "oauth_states"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    state_digest: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    code_verifier_encrypted: Mapped[str | None] = mapped_column(Text)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConnectorAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "connector_accounts"
    __table_args__ = (UniqueConstraint("user_id", "platform", name="uq_connector_user_platform"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    external_user_id: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    connector_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_cursor: Mapped[str | None] = mapped_column(Text)
    last_error: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="connectors")


class PlatformContent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_content"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", "external_id", name="uq_platform_content_identity"),
        Index("ix_platform_content_user_platform_published", "user_id", "platform", "published_at"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    connector_id: Mapped[str | None] = mapped_column(
        ForeignKey("connector_accounts.id", ondelete="SET NULL"), index=True
    )
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    author_external_id: Mapped[str | None] = mapped_column(String(255))
    author_name: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_own: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_method: Mapped[str] = mapped_column(String(40), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_records"
    __table_args__ = (
        Index("ix_memory_user_category_status", "user_id", "category", "evidence_status"),
        Index("ix_memory_user_visibility", "user_id", "visibility"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    visibility: Mapped[str] = mapped_column(String(40), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(40), nullable=False, default="none")
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    source_content_id: Mapped[str | None] = mapped_column(
        ForeignKey("platform_content.id", ondelete="SET NULL"), index=True
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    record_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(PortableVector())
    supersedes_id: Mapped[str | None] = mapped_column(
        ForeignKey("memory_records.id", ondelete="SET NULL"), index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_links"
    __table_args__ = (
        UniqueConstraint("from_record_id", "to_record_id", "relation", name="uq_memory_link"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    from_record_id: Mapped[str] = mapped_column(
        ForeignKey("memory_records.id", ondelete="CASCADE"), index=True
    )
    to_record_id: Mapped[str] = mapped_column(
        ForeignKey("memory_records.id", ondelete="CASCADE"), index=True
    )
    relation: Mapped[str] = mapped_column(String(80), nullable=False)
    link_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class Goal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_audiences: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    success_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RelationshipRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "relationship_records"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "platform", "external_person_id", name="uq_relationship_person"
        ),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_person_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_url: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="observed_participant")
    shared_context: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_meaningful_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)


class ResearchPacket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_packets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[str | None] = mapped_column(ForeignKey("goals.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    freshness_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    packet_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class ResearchItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_items"

    packet_id: Mapped[str] = mapped_column(
        ForeignKey("research_packets.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_content_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    audience_relevance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    recommended_stance: Mapped[str] = mapped_column(String(40), nullable=False, default="observe")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    item_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class StrategyVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strategy_versions"
    __table_args__ = (UniqueConstraint("user_id", "version", name="uq_strategy_user_version"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    positioning: Mapped[str] = mapped_column(Text, nullable=False)
    content_pillars: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    audience_priorities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    platform_tactics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    relationship_approach: Mapped[str] = mapped_column(Text, nullable=False, default="")
    excluded_tactics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    previous_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_versions.id", ondelete="SET NULL")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Hypothesis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hypotheses"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_versions.id", ondelete="SET NULL"), index=True
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(32))
    target_audience: Mapped[str] = mapped_column(String(300), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    success_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    measurement_window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (Index("ix_recommendation_user_status", "user_id", "status"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="SET NULL"), index=True
    )
    strategy_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("strategy_versions.id", ondelete="SET NULL")
    )
    hypothesis_id: Mapped[str | None] = mapped_column(
        ForeignKey("hypotheses.id", ondelete="SET NULL")
    )
    action_type: Mapped[str] = mapped_column(String(48), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(String(300), nullable=False)
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    draft: Mapped[str | None] = mapped_column(Text)
    final_text: Mapped[str | None] = mapped_column(Text)
    effort_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    unknowns: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReviewFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_feedback"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_category: Mapped[str | None] = mapped_column(String(80))
    reason_text: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="this_only")
    original_text: Mapped[str | None] = mapped_column(Text)
    final_text: Mapped[str | None] = mapped_column(Text)


class ActionRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "action_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    public_url: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(String(512))
    verification_source: Mapped[str | None] = mapped_column(String(80))
    measurement_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    action_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class MetricSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint("action_id", "captured_at", name="uq_metric_action_captured"),
    )

    action_id: Mapped[str] = mapped_column(
        ForeignKey("action_records.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_hours: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict[str, float | int | None]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    visible_participants: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    completeness: Mapped[str] = mapped_column(String(40), nullable=False, default="partial")


class OutcomeRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outcome_records"

    action_id: Mapped[str] = mapped_column(
        ForeignKey("action_records.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    audience_fit: Mapped[str] = mapped_column(Text, nullable=False)
    relationship_outcome: Mapped[str | None] = mapped_column(Text)
    career_outcome: Mapped[str | None] = mapped_column(Text)
    baseline_comparison: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis_result: Mapped[str] = mapped_column(String(40), nullable=False)
    uncertainty: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)


class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (Index("ix_workflow_user_kind_status", "user_id", "kind", "status"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    current_node: Mapped[str | None] = mapped_column(String(128))
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    interrupt_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DomainEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "domain_events"
    __table_args__ = (Index("ix_event_status_available", "status", "available_at"),)

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(80), nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), nullable=False)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
