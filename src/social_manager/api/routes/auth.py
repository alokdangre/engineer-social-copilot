from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from social_manager.api.dependencies import SessionDependency, SettingsDependency
from social_manager.domain.schemas import AccessToken, UserCreate, UserRead
from social_manager.security import create_access_token
from social_manager.services.users import UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(
    response: Response, access_token: str, settings: SettingsDependency
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=access_token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: SessionDependency) -> UserRead:
    try:
        user = await UserService().create(session, data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.post("/token", response_model=AccessToken)
async def token(
    response: Response,
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
    access_token = create_access_token(user.id, settings)
    _set_session_cookie(response, access_token, settings)
    return AccessToken(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, settings: SettingsDependency) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )
