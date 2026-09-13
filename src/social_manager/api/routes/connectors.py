from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from social_manager.api.dependencies import CurrentUser, SessionDependency, SettingsDependency
from social_manager.connectors.base import ConnectorError
from social_manager.domain.enums import Platform
from social_manager.domain.schemas import (
    ConnectorAuthorization,
    ConnectorRead,
    ConnectorSyncResult,
    ConnectorTokenInput,
)
from social_manager.services.connectors import (
    ConnectorConfigurationError,
    ConnectorNotFoundError,
    ConnectorService,
    OAuthStateError,
)

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("", response_model=list[ConnectorRead])
async def list_connectors(session: SessionDependency, user: CurrentUser) -> list[ConnectorRead]:
    records = await ConnectorService().list(session, user.id)
    return [ConnectorRead.model_validate(item) for item in records]


@router.post("/{platform}/authorize", response_model=ConnectorAuthorization)
async def authorize_connector(
    platform: Platform, session: SessionDependency, user: CurrentUser
) -> ConnectorAuthorization:
    if platform not in {Platform.GITHUB, Platform.X, Platform.LINKEDIN}:
        raise HTTPException(status_code=400, detail="This platform cannot be connected")
    try:
        return await ConnectorService().authorize(session, user.id, platform)
    except ConnectorConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _oauth_result_redirect(
    settings: SettingsDependency,
    platform: Platform,
    result: str,
) -> RedirectResponse:
    query = urlencode({"platform": platform.value, "result": result})
    location = f"{settings.frontend_app_url.rstrip('/')}/connectors?{query}"
    return RedirectResponse(location, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: Platform,
    session: SessionDependency,
    settings: SettingsDependency,
    code: str | None = Query(default=None, min_length=1),
    state_value: str | None = Query(default=None, alias="state", min_length=1),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    if error is not None:
        return _oauth_result_redirect(settings, platform, "denied")
    if code is None or state_value is None:
        return _oauth_result_redirect(settings, platform, "invalid_callback")
    try:
        await ConnectorService().complete_oauth(
            session, platform, code=code, state=state_value
        )
    except OAuthStateError:
        return _oauth_result_redirect(settings, platform, "invalid_state")
    except ConnectorConfigurationError:
        return _oauth_result_redirect(settings, platform, "not_configured")
    except ConnectorError:
        return _oauth_result_redirect(settings, platform, "provider_error")
    return _oauth_result_redirect(settings, platform, "success")


@router.post("/{platform}/token", response_model=ConnectorRead)
async def connect_with_token(
    platform: Platform,
    data: ConnectorTokenInput,
    session: SessionDependency,
    user: CurrentUser,
) -> ConnectorRead:
    if platform not in {Platform.GITHUB, Platform.X, Platform.LINKEDIN}:
        raise HTTPException(status_code=400, detail="This platform cannot be connected")
    try:
        account = await ConnectorService().connect_token(session, user.id, platform, data)
    except ConnectorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ConnectorRead.model_validate(account)


@router.post("/{platform}/sync", response_model=ConnectorSyncResult)
async def sync_connector(
    platform: Platform, session: SessionDependency, user: CurrentUser
) -> ConnectorSyncResult:
    try:
        return await ConnectorService().sync(session, user.id, platform)
    except ConnectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConnectorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{platform}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_connector(
    platform: Platform, session: SessionDependency, user: CurrentUser
) -> None:
    try:
        await ConnectorService().disconnect(session, user.id, platform)
    except ConnectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
