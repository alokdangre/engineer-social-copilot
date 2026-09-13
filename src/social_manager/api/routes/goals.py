from fastapi import APIRouter, status
from sqlalchemy import select

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.db.models import Goal
from social_manager.domain.schemas import GoalCreate, GoalRead

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(data: GoalCreate, session: SessionDependency, user: CurrentUser) -> GoalRead:
    goal = Goal(user_id=user.id, **data.model_dump())
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return GoalRead.model_validate(goal)


@router.get("", response_model=list[GoalRead])
async def list_goals(session: SessionDependency, user: CurrentUser) -> list[GoalRead]:
    records = await session.scalars(
        select(Goal).where(Goal.user_id == user.id).order_by(Goal.priority.desc())
    )
    return [GoalRead.model_validate(item) for item in records]
