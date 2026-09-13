from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.db.models import ActionRecord, Recommendation
from social_manager.domain.enums import RecommendationStatus
from social_manager.domain.schemas import (
    ActionPerformedInput,
    ActionRead,
    MetricsInput,
    RecommendationRead,
    ReviewInput,
)
from social_manager.services.recommendations import (
    InvalidRecommendationTransition,
    RecommendationNotFoundError,
    RecommendationService,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations and actions"])


@router.get("", response_model=list[RecommendationRead])
async def list_recommendations(
    session: SessionDependency,
    user: CurrentUser,
    recommendation_status: RecommendationStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RecommendationRead]:
    records = await RecommendationService().list(
        session, user.id, status=recommendation_status, limit=limit
    )
    return [RecommendationRead.model_validate(item) for item in records]


@router.post("/{recommendation_id}/review", response_model=RecommendationRead)
async def review_recommendation(
    recommendation_id: str,
    data: ReviewInput,
    session: SessionDependency,
    user: CurrentUser,
) -> RecommendationRead:
    try:
        recommendation = await RecommendationService().review(
            session, user.id, recommendation_id, data
        )
    except RecommendationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidRecommendationTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RecommendationRead.model_validate(recommendation)


@router.post("/{recommendation_id}/performed", response_model=ActionRead)
async def report_performed(
    recommendation_id: str,
    data: ActionPerformedInput,
    session: SessionDependency,
    user: CurrentUser,
) -> ActionRead:
    try:
        action = await RecommendationService().report_performed(
            session, user.id, recommendation_id, data
        )
    except RecommendationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidRecommendationTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ActionRead.model_validate(action)


@router.post("/actions/{action_id}/metrics", status_code=201)
async def add_metrics(
    action_id: str,
    data: MetricsInput,
    session: SessionDependency,
    user: CurrentUser,
) -> dict[str, str]:
    action = await session.get(ActionRecord, action_id)
    if action is None or action.user_id != user.id:
        raise HTTPException(status_code=404, detail="Action not found")
    recommendation = await session.get(Recommendation, action.recommendation_id)
    if recommendation is None or not recommendation.platform:
        raise HTTPException(status_code=400, detail="Action has no measurable social platform")
    try:
        snapshot = await RecommendationService().add_metrics(
            session, user.id, action_id, recommendation.platform, data
        )
    except InvalidRecommendationTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"metric_snapshot_id": snapshot.id}


@router.get("/actions", response_model=list[ActionRead])
async def list_actions(
    session: SessionDependency,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ActionRead]:
    records = await session.scalars(
        select(ActionRecord)
        .where(ActionRecord.user_id == user.id)
        .order_by(ActionRecord.created_at.desc())
        .limit(limit)
    )
    return [ActionRead.model_validate(item) for item in records]
