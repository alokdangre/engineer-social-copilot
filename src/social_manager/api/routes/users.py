from fastapi import APIRouter, status

from social_manager.api.dependencies import CurrentUser, SessionDependency
from social_manager.domain.schemas import (
    LLMCredentialInput,
    LLMCredentialRead,
    UserRead,
    UserUpdate,
)
from social_manager.services.llm_credentials import LLMCredentialService
from social_manager.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, session: SessionDependency, user: CurrentUser) -> UserRead:
    updated = await UserService().update(session, user, data)
    return UserRead.model_validate(updated)


@router.get("/me/llm-credential", response_model=LLMCredentialRead)
async def get_llm_credential(
    session: SessionDependency,
    user: CurrentUser,
) -> LLMCredentialRead:
    return await LLMCredentialService().describe(session, user.id)


@router.put("/me/llm-credential", response_model=LLMCredentialRead)
async def save_llm_credential(
    data: LLMCredentialInput,
    session: SessionDependency,
    user: CurrentUser,
) -> LLMCredentialRead:
    return await LLMCredentialService().upsert(session, user.id, data)


@router.delete("/me/llm-credential", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_credential(
    session: SessionDependency,
    user: CurrentUser,
) -> None:
    await LLMCredentialService().delete(session, user.id)
