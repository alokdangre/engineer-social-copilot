from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.config import Settings, get_settings
from social_manager.db.models import User
from social_manager.db.session import get_session
from social_manager.security import AuthenticationError, decode_access_token
from social_manager.services.users import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

SessionDependency = Annotated[AsyncSession, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


async def get_current_user(
    session: SessionDependency,
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: SettingsDependency,
) -> User:
    try:
        user_id = decode_access_token(token, settings)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = await UserService().get(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
