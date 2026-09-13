from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.agent.schemas import (
    EcosystemAnalysis,
    HypothesisCandidate,
    RecommendationCandidate,
    ResearchFinding,
)
from social_manager.db.models import PlatformContent, User
from social_manager.domain.enums import (
    ActionType,
    ContentType,
    EvidenceStatus,
    FeedbackScope,
    MemoryCategory,
    Platform,
    RecommendationStatus,
    ReviewDecision,
    SourceAccessMethod,
    Visibility,
)
from social_manager.domain.schemas import (
    ActionPerformedInput,
    MemoryCreate,
    MemoryLinkCreate,
    MemoryUpdate,
    MetricsInput,
    PlatformContentCreate,
    ReviewInput,
    UserCreate,
    UserUpdate,
)
from social_manager.services.content import ContentService
from social_manager.services.events import EventService
from social_manager.services.memory import MemoryNotFoundError, MemoryService
from social_manager.services.recommendations import (
    InvalidRecommendationTransition,
    RecommendationService,
)
from social_manager.services.research import ResearchService
from social_manager.services.strategy import StrategyService
from social_manager.services.users import UserAlreadyExistsError, UserService


@pytest.mark.asyncio
async def test_user_service(db_session: AsyncSession) -> None:
    svc = UserService()
    user = await svc.create(
        db_session,
        UserCreate(
            email="svc_user@example.com",
            display_name="Service User",
            password="StrongPassword123!",
        ),
    )
    assert user.id is not None
    assert user.email == "svc_user@example.com"

    # Duplicate registration raises UserAlreadyExistsError
    with pytest.raises(UserAlreadyExistsError):
        await svc.create(
            db_session,
            UserCreate(
                email="svc_user@example.com",
                display_name="Other",
                password="Pass12345678!",
            ),
        )

    # Authentication success
    authed = await svc.authenticate(db_session, "svc_user@example.com", "StrongPassword123!")
    assert authed is not None
    assert authed.id == user.id

    # Authentication failure returns None
    failed = await svc.authenticate(db_session, "svc_user@example.com", "WrongPassword!")
    assert failed is None

    # Update user
    updated = await svc.update(db_session, user, UserUpdate(display_name="Updated Display Name"))
    assert updated.display_name == "Updated Display Name"


@pytest.mark.asyncio
async def test_memory_service(db_session: AsyncSession, test_user: User) -> None:
    svc = MemoryService()
    mem1 = await svc.create(
        db_session,
        test_user.id,
        MemoryCreate(
            category=MemoryCategory.TECHNICAL_KNOWLEDGE,
            title="FastAPI Async Lifespans",
            statement="FastAPI lifespans are cleaner than legacy startup events.",
            evidence_status=EvidenceStatus.USER_CONFIRMED,
            visibility=Visibility.APPROVED_PUBLIC,
        ),
    )
    assert mem1.id is not None

    mem2 = await svc.create(
        db_session,
        test_user.id,
        MemoryCreate(
            category=MemoryCategory.PROJECT_CONTRIBUTION,
            title="Built Social Manager Backend",
            statement="Implemented LangGraph workflows and FastAPI backend.",
            evidence_status=EvidenceStatus.OBSERVED,
            visibility=Visibility.POTENTIALLY_SHAREABLE,
        ),
    )

    # Link memories
    link = await svc.create_link(
        db_session,
        test_user.id,
        MemoryLinkCreate(
            from_record_id=mem1.id,
            to_record_id=mem2.id,
            relation="supports",
        ),
    )
    assert link.id is not None

    # List memories
    records = await svc.list(db_session, test_user.id, category=MemoryCategory.TECHNICAL_KNOWLEDGE)
    assert any(r.id == mem1.id for r in records)

    # Recommendation packet
    packet = await svc.recommendation_packet(db_session, test_user.id, query="FastAPI")
    assert len(packet) >= 1

    # Update memory
    updated = await svc.update(
        db_session,
        test_user.id,
        mem1.id,
        MemoryUpdate(title="FastAPI Lifespans Updated"),
    )
    assert updated.title == "FastAPI Lifespans Updated"

    # Soft delete
    await svc.soft_delete(db_session, test_user.id, mem2.id)
    with pytest.raises(MemoryNotFoundError):
        await svc.get_owned(db_session, test_user.id, mem2.id)


@pytest.mark.asyncio
async def test_content_service(db_session: AsyncSession, test_user: User) -> None:
    svc = ContentService()
    content_in = PlatformContentCreate(
        platform=Platform.GITHUB,
        external_id="gh_issue_99",
        content_type=ContentType.ISSUE,
        title="Async bug in connector",
        body="Reproduction details...",
        access_method=SourceAccessMethod.OFFICIAL_API,
        is_own=True,
    )
    content, created = await svc.upsert(db_session, test_user.id, content_in)
    assert created is True
    assert content.id is not None

    # Upsert duplicate external_id
    content2, created2 = await svc.upsert(db_session, test_user.id, content_in)
    assert created2 is False
    assert content2.id == content.id

    found = await db_session.scalar(
        select(PlatformContent).where(
            PlatformContent.user_id == test_user.id,
            PlatformContent.external_id == "gh_issue_99",
        )
    )
    assert found is not None
    assert found.id == content.id


@pytest.mark.asyncio
async def test_research_service(db_session: AsyncSession, test_user: User) -> None:
    svc = ResearchService()
    analysis = EcosystemAnalysis(
        summary="Python 3.12 adoption is accelerating.",
        coverage_notes="Based on GitHub pull requests and technical posts.",
        findings=[
            ResearchFinding(
                kind="trend",
                title="Python 3.12 Generics",
                description="Inline generic syntax reduces boilerplate.",
                source_urls=["https://github.com/python/cpython"],
                audience_relevance=0.85,
                confidence=0.8,
                recommended_stance="observe",
            )
        ],
        hypotheses=[],
    )
    packet = await svc.create_packet(db_session, test_user.id, analysis)
    assert packet.id is not None

    latest, items = await svc.latest_packet(db_session, test_user.id)
    assert latest is not None
    assert len(items) == 1
    assert items[0].title == "Python 3.12 Generics"


@pytest.mark.asyncio
async def test_recommendations_and_actions(db_session: AsyncSession, test_user: User) -> None:
    svc = RecommendationService()
    candidate = RecommendationCandidate(
        action_type=ActionType.ORIGINAL_POST,
        platform=Platform.X,
        title="Share Async Lesson",
        purpose="Explain how structured concurrency prevents task leaks.",
        target_audience="Backend Python engineers",
        why_now="Recent GitHub commit showed a clean concurrency fix.",
        draft="Structured concurrency in Python prevents task leaks. Here is how...",
        effort_minutes=15,
        score=0.85,
    )
    recs = await svc.create_many(db_session, test_user.id, [candidate])
    assert len(recs) == 1
    rec = recs[0]
    assert rec.status == RecommendationStatus.AWAITING_REVIEW.value

    # Review: Edit
    reviewed = await svc.review(
        db_session,
        test_user.id,
        rec.id,
        ReviewInput(
            decision=ReviewDecision.EDIT,
            final_text="Edited: Structured concurrency in Python is awesome.",
            scope=FeedbackScope.THIS_ONLY,
            reason_category="voice_adjustment",
        ),
    )
    assert reviewed.status == RecommendationStatus.EDITED.value
    assert reviewed.final_text == "Edited: Structured concurrency in Python is awesome."

    # Cannot review already reviewed recommendation
    with pytest.raises(InvalidRecommendationTransition):
        await svc.review(
            db_session,
            test_user.id,
            rec.id,
            ReviewInput(decision=ReviewDecision.APPROVE),
        )

    # Report performed
    action = await svc.report_performed(
        db_session,
        test_user.id,
        rec.id,
        ActionPerformedInput(
            public_url="https://x.com/testdev/status/123456",
            external_id="123456",
            notes="Manually published post.",
        ),
    )
    assert action.status == RecommendationStatus.REPORTED_PERFORMED.value
    assert action.measurement_due_at is not None

    # Add metrics
    metric = await svc.add_metrics(
        db_session,
        test_user.id,
        action.id,
        platform=Platform.X.value,
        data=MetricsInput(
            metrics={"impressions": 1200, "likes": 42, "replies": 5},
            visible_participants=[{"handle": "@maintainer1"}, {"handle": "@founder2"}],
            source="user_reported",
        ),
    )
    assert metric.id is not None
    assert metric.metrics["impressions"] == 1200


@pytest.mark.asyncio
async def test_strategy_service(db_session: AsyncSession, test_user: User) -> None:
    svc = StrategyService()
    strat = await svc.ensure_initial(
        db_session,
        test_user.id,
        positioning="Credible Systems & Backend Engineer",
        content_pillars=["Async Architectures", "Reliability", "Open Source Lessons"],
        audience_priorities=["Staff Engineers", "Engineering Leads"],
        rationale="Initial baseline from onboarding analysis",
    )
    assert strat.version == 1
    assert strat.status == "active"

    # Current
    current = await svc.current(db_session, test_user.id)
    assert current is not None
    assert current.id == strat.id

    # Record hypothesis via create_hypotheses
    hypotheses = await svc.create_hypotheses(
        db_session,
        test_user.id,
        [
            HypothesisCandidate(
                statement=(
                    "Detailed architectural posts perform better on LinkedIn than short updates."
                ),
                observation="Observed on engineering leadership feeds.",
                platform=Platform.LINKEDIN,
                target_audience="Engineering Leads",
                expected_outcome="Substantive replies from engineering leaders",
                confidence=0.6,
            )
        ],
        strategy_version_id=strat.id,
    )
    assert len(hypotheses) == 1
    assert hypotheses[0].id is not None

    # Propose update via next_version
    proposed = await svc.next_version(
        db_session,
        test_user.id,
        proposed_changes=["Focus on deep architectural writeups for LinkedIn"],
        rationale="Hypothesis validation from recent engagement",
    )
    assert proposed.version == 2
    assert proposed.status == "proposed"

    # Activate version 2
    activated = await svc.activate(db_session, test_user.id, proposed.id)
    assert activated.status == "active"
    current_after = await svc.current(db_session, test_user.id)
    assert current_after is not None
    assert current_after.version == 2


@pytest.mark.asyncio
async def test_event_service(db_session: AsyncSession, test_user: User) -> None:
    svc = EventService()
    event = await svc.emit(
        db_session,
        event_type="workflow_completed",
        aggregate_type="workflow",
        aggregate_id="wf_101",
        user_id=test_user.id,
        payload={"result": "success"},
    )
    assert event.id is not None
    assert event.event_type == "workflow_completed"
    assert event.status == "pending"
