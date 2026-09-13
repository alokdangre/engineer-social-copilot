from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy import select

from social_manager.agent.context import load_user_context
from social_manager.agent.model_gateway import ModelGateway
from social_manager.agent.schemas import MemoryCandidate, ProfileAnalysis
from social_manager.agent.state import ProfileState
from social_manager.db.models import Goal
from social_manager.db.session import database
from social_manager.domain.enums import (
    EvidenceStatus,
    MemoryCategory,
    Platform,
    ReviewDecision,
    Visibility,
)
from social_manager.domain.schemas import MemoryCreate
from social_manager.services.memory import MemoryService
from social_manager.services.strategy import StrategyService

PROFILE_SYSTEM_PROMPT = """
Build an evidence-conscious baseline for a technical professional. Separate observed facts,
self-reported information, and inferences. Never infer mastery, sole authorship, production impact,
or career outcomes from repository presence. Describe missing evidence and ask focused confirmation
questions. Return only the requested structured schema.
""".strip()


def build_profile_graph(
    model_gateway: ModelGateway | None = None,
    memory_service: MemoryService | None = None,
    strategy_service: StrategyService | None = None,
) -> StateGraph[ProfileState]:
    model = model_gateway or ModelGateway()
    memories = memory_service or MemoryService(model)
    strategies = strategy_service or StrategyService()

    async def collect_sources(state: ProfileState) -> dict[str, Any]:
        async with database.session_factory() as session:
            context = await load_user_context(session, state["user_id"])
        context["stated_input"] = state.get("input", {})
        return {"source_context": context}

    async def analyze_profile(state: ProfileState) -> dict[str, Any]:
        context = state["source_context"]
        fallback = _fallback_profile(context)
        analysis = await model.generate(
            ProfileAnalysis,
            system_prompt=PROFILE_SYSTEM_PROMPT,
            payload={"source_context": context},
            fallback=fallback,
            user_id=state["user_id"],
        )
        return {"profile_analysis": analysis.model_dump(mode="json")}

    def review_profile(state: ProfileState) -> dict[str, Any]:
        review = interrupt(
            {
                "type": "profile_baseline_review",
                "message": "Confirm, edit, reject, or postpone this evidence-backed baseline.",
                "analysis": state["profile_analysis"],
                "allowed_decisions": [decision.value for decision in ReviewDecision],
            }
        )
        if not isinstance(review, dict):
            raise ValueError("Profile review must be an object")
        raw_decision = review.get("decision")
        if not isinstance(raw_decision, str):
            raise ValueError("Profile review must include a string 'decision'")
        decision = ReviewDecision(raw_decision)
        return {"review": {**review, "decision": decision.value}}

    def route_review(state: ProfileState) -> str:
        return (
            "persist_baseline"
            if state["review"]["decision"] in {ReviewDecision.APPROVE, ReviewDecision.EDIT}
            else END
        )

    async def persist_baseline(state: ProfileState) -> dict[str, Any]:
        analysis = ProfileAnalysis.model_validate(state["profile_analysis"])
        review = state["review"]
        candidates = [*analysis.credible_skills, *analysis.projects, *analysis.voice_observations]
        memory_inputs = [_confirmed_memory(candidate) for candidate in candidates]
        for index, journey_item in enumerate(analysis.software_journey):
            memory_inputs.append(
                MemoryCreate(
                    category=MemoryCategory.EVENT_EXPERIENCE,
                    title=f"Software journey item {index + 1}",
                    statement=journey_item,
                    evidence_status=EvidenceStatus.INFERRED,
                    confidence=0.6,
                    visibility=Visibility.POTENTIALLY_SHAREABLE,
                    source_platform=Platform.USER,
                    metadata={"origin": "profile_baseline"},
                )
            )
        for correction in review.get("corrections", []):
            if isinstance(correction, dict) and correction.get("statement"):
                memory_inputs.append(
                    MemoryCreate(
                        category=MemoryCategory(correction.get("category", "identity_preference")),
                        title=str(correction.get("title", "User correction"))[:300],
                        statement=str(correction["statement"]),
                        evidence_status=EvidenceStatus.USER_CONFIRMED,
                        confidence=1.0,
                        visibility=Visibility(
                            correction.get("visibility", "potentially_shareable")
                        ),
                        source_platform=Platform.USER,
                        metadata={"origin": "profile_review_correction"},
                    )
                )
        async with database.session_factory() as session:
            records = await memories.create_many(session, state["user_id"], memory_inputs)
            input_data = state.get("input", {})
            for raw_goal in input_data.get("goals", []):
                if not isinstance(raw_goal, dict) or not raw_goal.get("title"):
                    continue
                existing = await session.scalar(
                    select(Goal).where(
                        Goal.user_id == state["user_id"], Goal.title == str(raw_goal["title"])
                    )
                )
                if existing is None:
                    session.add(
                        Goal(
                            user_id=state["user_id"],
                            title=str(raw_goal["title"])[:300],
                            description=str(raw_goal.get("description", raw_goal["title"])),
                            target_audiences=list(raw_goal.get("target_audiences", [])),
                            success_criteria=list(raw_goal.get("success_criteria", [])),
                            priority=int(raw_goal.get("priority", 50)),
                        )
                    )
            await session.commit()
            strategy = await strategies.ensure_initial(
                session,
                state["user_id"],
                positioning=analysis.positioning,
                content_pillars=analysis.content_pillars,
                audience_priorities=list(input_data.get("target_audiences", [])),
                rationale="Initial user-confirmed profile baseline",
            )
        return {
            "memory_ids": [record.id for record in records],
            "strategy_id": strategy.id,
            "output": {
                "status": "confirmed",
                "memory_ids": [record.id for record in records],
                "strategy_id": strategy.id,
            },
        }

    builder = StateGraph(ProfileState)
    builder.add_node("collect_sources", collect_sources)
    builder.add_node("analyze_profile", analyze_profile)
    builder.add_node("review_profile", review_profile)
    builder.add_node("persist_baseline", persist_baseline)
    builder.add_edge(START, "collect_sources")
    builder.add_edge("collect_sources", "analyze_profile")
    builder.add_edge("analyze_profile", "review_profile")
    builder.add_conditional_edges("review_profile", route_review, ["persist_baseline", END])
    builder.add_edge("persist_baseline", END)
    return builder


def _fallback_profile(context: dict[str, Any]) -> ProfileAnalysis:
    repositories = [
        item for item in context.get("content", []) if item.get("content_type") == "repository"
    ]
    projects: list[MemoryCandidate] = []
    skill_names: set[str] = set()
    journey: list[str] = []
    for repository in repositories[:20]:
        data = repository.get("normalized_data", {})
        name = data.get("full_name") or data.get("name") or "GitHub project"
        language = data.get("language")
        projects.append(
            MemoryCandidate(
                category=MemoryCategory.PROJECT_CONTRIBUTION,
                title=str(name),
                statement=(
                    f"GitHub shows the repository {name}. Its presence does not by itself prove "
                    "sole authorship, mastery, or production impact."
                ),
                evidence_status=EvidenceStatus.OBSERVED,
                confidence=0.8,
                visibility=Visibility.POTENTIALLY_SHAREABLE,
                source_platform=Platform.GITHUB,
                source_reference=repository.get("url"),
                metadata={"content_id": repository.get("id")},
            )
        )
        if language:
            skill_names.add(str(language))
        if repository.get("published_at"):
            journey.append(f"Created or began {name} around {repository['published_at'][:10]}.")
    skills = [
        MemoryCandidate(
            category=MemoryCategory.TECHNICAL_KNOWLEDGE,
            title=f"Experience with {name}",
            statement=f"{name} appears in at least one connected GitHub repository.",
            evidence_status=EvidenceStatus.INFERRED,
            confidence=0.55,
            visibility=Visibility.POTENTIALLY_SHAREABLE,
            source_platform=Platform.GITHUB,
        )
        for name in sorted(skill_names)
    ]
    goals = context.get("goals", [])
    stated = context.get("stated_input", {})
    audiences = stated.get("target_audiences", [])
    positioning = (
        str(stated.get("positioning"))
        if stated.get("positioning")
        else "Technical professional documenting real work and useful lessons"
    )
    questions = []
    if not repositories:
        questions.append("Which projects best represent your current skills and intended niche?")
    if not goals and not stated.get("goals"):
        questions.append("What outcome matters most: reputation, DevRel, a role, or collaboration?")
    if not audiences:
        questions.append("Which audience should recognize your work first?")
    return ProfileAnalysis(
        software_journey=journey,
        credible_skills=skills,
        projects=projects,
        voice_observations=[],
        positioning=positioning,
        content_pillars=[
            "project evidence",
            "technical lessons",
            "learning and experiments",
            "open-source and community participation",
        ],
        inconsistencies=[],
        confirmation_questions=questions,
    )


def _confirmed_memory(candidate: MemoryCandidate) -> MemoryCreate:
    return MemoryCreate(
        category=candidate.category,
        title=candidate.title,
        statement=candidate.statement,
        evidence_status=(
            EvidenceStatus.USER_CONFIRMED
            if candidate.evidence_status != EvidenceStatus.OBSERVED
            else EvidenceStatus.OBSERVED
        ),
        confidence=max(candidate.confidence, 0.8),
        visibility=candidate.visibility,
        sensitivity=candidate.sensitivity,
        source_platform=candidate.source_platform,
        source_reference=candidate.source_reference,
        observed_at=datetime.now(UTC),
        metadata={**candidate.metadata, "confirmed_in_profile_review": True},
    )


profile_graph = build_profile_graph().compile()
