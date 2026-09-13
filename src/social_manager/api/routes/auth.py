from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from social_manager.api.dependencies import SessionDependency, SettingsDependency
from social_manager.domain.schemas import AccessToken, UserCreate, UserRead
from social_manager.security import create_access_token
from social_manager.services.users import UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: SessionDependency) -> UserRead:
    try:
        user = await UserService().create(session, data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.post("/token", response_model=AccessToken)
async def token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDependency,
    settings: SettingsDependency,
) -> AccessToken:
    user = await UserService().authenticate(session, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AccessToken(access_token=create_access_token(user.id, settings))
