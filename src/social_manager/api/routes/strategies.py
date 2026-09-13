from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.db.models import StrategyVersion
from social_manager.domain.schemas import HypothesisRead, StrategyRead
from social_manager.services.strategy import StrategyService

router = APIRouter(prefix="/strategies", tags=["strategy"])


@router.get("", response_model=list[StrategyRead])
async def list_strategies(
    session: SessionDependency,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[StrategyRead]:
    records = await session.scalars(
        select(StrategyVersion)
        .where(StrategyVersion.user_id == user.id)
        .order_by(StrategyVersion.version.desc())
        .limit(limit)
    )
    return [StrategyRead.model_validate(item) for item in records]


@router.get("/current", response_model=StrategyRead | None)
async def current_strategy(session: SessionDependency, user: CurrentUser) -> StrategyRead | None:
    strategy = await StrategyService().current(session, user.id)
    return StrategyRead.model_validate(strategy) if strategy else None


@router.get("/hypotheses", response_model=list[HypothesisRead])
async def list_hypotheses(
    session: SessionDependency,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[HypothesisRead]:
    records = await StrategyService().list_hypotheses(session, user.id, limit=limit)
    return [HypothesisRead.model_validate(item) for item in records]


@router.post("/{strategy_id}/activate", response_model=StrategyRead)
async def activate_strategy(
    strategy_id: str, session: SessionDependency, user: CurrentUser
) -> StrategyRead:
    try:
        strategy = await StrategyService().activate(session, user.id, strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StrategyRead.model_validate(strategy)
