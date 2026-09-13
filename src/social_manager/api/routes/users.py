from fastapi import APIRouter

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.domain.schemas import UserRead, UserUpdate
from social_manager.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, session: SessionDependency, user: CurrentUser) -> UserRead:
    updated = await UserService().update(session, user, data)
    return UserRead.model_validate(updated)
