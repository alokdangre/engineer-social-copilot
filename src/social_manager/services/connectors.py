from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.config import Settings, get_settings
from social_manager.connectors.base import BaseConnector, ConnectorError
from social_manager.connectors.github import GitHubConnector
from social_manager.connectors.linkedin import LinkedInConnector
from social_manager.connectors.x import XConnector
from social_manager.db.models import ConnectorAccount, OAuthState
from social_manager.domain.enums import (
    ConnectorStatus,
    Platform,
    SourceAccessMethod,
)
from social_manager.domain.schemas import (
    ConnectorAuthorization,
    ConnectorSyncResult,
    ConnectorTokenInput,
    PlatformContentCreate,
)
from social_manager.security import (
    TokenCipher,
    digest_oauth_state,
    generate_oauth_state,
    generate_pkce_pair,
)
from social_manager.services.content import ContentService


class ConnectorNotFoundError(ValueError):
    pass


class ConnectorConfigurationError(ValueError):
    pass


class OAuthStateError(ValueError):
    pass


class ConnectorService:
    def __init__(
        self,
        settings: Settings | None = None,
        cipher: TokenCipher | None = None,
        content_service: ContentService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.cipher = cipher or TokenCipher(self.settings)
        self.content_service = content_service or ContentService()

    async def list(self, session: AsyncSession, user_id: str) -> list[ConnectorAccount]:
        result = await session.scalars(
            select(ConnectorAccount)
            .where(ConnectorAccount.user_id == user_id)
            .order_by(ConnectorAccount.platform)
        )
        return list(result)

    async def authorize(
        self, session: AsyncSession, user_id: str, platform: Platform
    ) -> ConnectorAuthorization:
        state = generate_oauth_state()
        redirect_uri = self._redirect_uri(platform)
        verifier: str | None = None
        query: dict[str, str]
        if platform == Platform.GITHUB:
            client_id = self._require(self.settings.github_client_id, "GITHUB_CLIENT_ID")
            base_url = "https://github.com/login/oauth/authorize"
            query = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": "read:user user:email",
                "state": state,
            }
        elif platform == Platform.X:
            client_id = self._require(self.settings.x_client_id, "X_CLIENT_ID")
            verifier, challenge = generate_pkce_pair()
            base_url = "https://twitter.com/i/oauth2/authorize"
            query = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": "tweet.read users.read offline.access",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        elif platform == Platform.LINKEDIN:
            client_id = self._require(self.settings.linkedin_client_id, "LINKEDIN_CLIENT_ID")
            base_url = "https://www.linkedin.com/oauth/v2/authorization"
            query = {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid profile email r_member_postAnalytics",
                "state": state,
            }
        else:
            raise ConnectorConfigurationError(f"OAuth is not supported for {platform.value}")

        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        session.add(
            OAuthState(
                user_id=user_id,
                platform=platform.value,
                state_digest=digest_oauth_state(state),
                code_verifier_encrypted=self.cipher.encrypt(verifier) if verifier else None,
                redirect_uri=redirect_uri,
                expires_at=expires_at,
            )
        )
        await session.commit()
        return ConnectorAuthorization(
            platform=platform,
            authorization_url=f"{base_url}?{urlencode(query)}",
            expires_at=expires_at,
        )

    async def complete_oauth(
        self,
        session: AsyncSession,
        platform: Platform,
        *,
        code: str,
        state: str,
    ) -> ConnectorAccount:
        now = datetime.now(UTC)
        oauth_state = await session.scalar(
            select(OAuthState).where(
                OAuthState.platform == platform.value,
                OAuthState.state_digest == digest_oauth_state(state),
                OAuthState.consumed_at.is_(None),
                OAuthState.expires_at > now,
            )
        )
        if oauth_state is None:
            raise OAuthStateError("OAuth state is invalid, expired, or already used")
        oauth_state.consumed_at = now
        token = await self._exchange_code(platform, code, oauth_state)
        account = await self.connect_token(
            session,
            oauth_state.user_id,
            platform,
            ConnectorTokenInput(
                access_token=str(token["access_token"]),
                refresh_token=token.get("refresh_token"),
                expires_at=(
                    now + timedelta(seconds=int(token["expires_in"]))
                    if token.get("expires_in")
                    else None
                ),
                scopes=str(token.get("scope", "")).split(),
            ),
        )
        await session.commit()
        return account

    async def connect_token(
        self,
        session: AsyncSession,
        user_id: str,
        platform: Platform,
        token: ConnectorTokenInput,
    ) -> ConnectorAccount:
        client = self._client(platform, token.access_token)
        identity = await client.get_identity()
        account = await session.scalar(
            select(ConnectorAccount).where(
                ConnectorAccount.user_id == user_id,
                ConnectorAccount.platform == platform.value,
            )
        )
        if account is None:
            account = ConnectorAccount(
                user_id=user_id,
                platform=platform.value,
                encrypted_access_token=self.cipher.encrypt(token.access_token),
            )
            session.add(account)
        account.status = ConnectorStatus.CONNECTED.value
        account.external_user_id = identity.external_user_id
        account.username = identity.username
        account.encrypted_access_token = self.cipher.encrypt(token.access_token)
        account.encrypted_refresh_token = (
            self.cipher.encrypt(token.refresh_token) if token.refresh_token else None
        )
        account.token_expires_at = token.expires_at
        account.scopes = token.scopes
        account.connector_metadata = identity.metadata
        account.last_error = None
        await session.commit()
        await session.refresh(account)
        return account

    async def disconnect(self, session: AsyncSession, user_id: str, platform: Platform) -> None:
        account = await self.get_owned(session, user_id, platform)
        await session.delete(account)
        await session.commit()

    async def sync(
        self, session: AsyncSession, user_id: str, platform: Platform
    ) -> ConnectorSyncResult:
        account = await self.get_owned(session, user_id, platform)
        try:
            client = self._client(platform, self.cipher.decrypt(account.encrypted_access_token))
            batch = await client.sync_own_content(account.last_sync_cursor)
            created = 0
            updated = 0
            for external in batch.content:
                retention_expires_at = None
                if platform == Platform.LINKEDIN:
                    retention_expires_at = datetime.now(UTC) + timedelta(
                        hours=self.settings.default_research_retention_hours
                    )
                _, was_created = await self.content_service.upsert(
                    session,
                    user_id,
                    PlatformContentCreate(
                        platform=external.platform,
                        external_id=external.external_id,
                        content_type=external.content_type,
                        author_external_id=external.author_external_id,
                        author_name=external.author_name,
                        body=external.body,
                        url=external.url,
                        published_at=external.published_at,
                        metrics=external.metrics,
                        normalized_data=external.normalized_data,
                        is_own=external.is_own,
                        access_method=SourceAccessMethod.OFFICIAL_API,
                        retention_expires_at=retention_expires_at,
                    ),
                    connector_id=account.id,
                )
                created += int(was_created)
                updated += int(not was_created)
            account.external_user_id = (
                batch.identity.external_user_id if batch.identity else account.external_user_id
            )
            account.username = batch.identity.username if batch.identity else account.username
            account.last_sync_at = datetime.now(UTC)
            account.last_sync_cursor = batch.cursor
            account.last_error = None
            account.status = ConnectorStatus.CONNECTED.value
            await session.commit()
            return ConnectorSyncResult(
                platform=platform,
                fetched=len(batch.content),
                created=created,
                updated=updated,
                cursor=batch.cursor,
                warnings=batch.warnings,
            )
        except Exception as exc:
            account.last_error = str(exc)[:2000]
            account.status = (
                ConnectorStatus.EXPIRED.value
                if isinstance(exc, ConnectorError) and exc.status_code in {401, 403}
                else ConnectorStatus.ERROR.value
            )
            await session.commit()
            raise

    async def get_owned(
        self, session: AsyncSession, user_id: str, platform: Platform
    ) -> ConnectorAccount:
        account = await session.scalar(
            select(ConnectorAccount).where(
                ConnectorAccount.user_id == user_id,
                ConnectorAccount.platform == platform.value,
            )
        )
        if account is None:
            raise ConnectorNotFoundError(f"{platform.value} is not connected")
        return account

    def _client(self, platform: Platform, access_token: str) -> BaseConnector:
        connector_types: dict[Platform, type[BaseConnector]] = {
            Platform.GITHUB: GitHubConnector,
            Platform.X: XConnector,
            Platform.LINKEDIN: LinkedInConnector,
        }
        connector_type = connector_types.get(platform)
        if connector_type is None:
            raise ConnectorConfigurationError(f"No connector client for {platform.value}")
        return connector_type(access_token, settings=self.settings)

    def _redirect_uri(self, platform: Platform) -> str:
        return f"{self.settings.oauth_callback_base_url.rstrip('/')}/{platform.value}/callback"

    async def _exchange_code(
        self, platform: Platform, code: str, oauth_state: OAuthState
    ) -> dict[str, Any]:
        if platform == Platform.GITHUB:
            url = "https://github.com/login/oauth/access_token"
            data = {
                "client_id": self._require(self.settings.github_client_id, "GITHUB_CLIENT_ID"),
                "client_secret": self._require_secret(
                    self.settings.github_client_secret, "GITHUB_CLIENT_SECRET"
                ),
                "code": code,
                "redirect_uri": oauth_state.redirect_uri,
            }
            auth = None
        elif platform == Platform.X:
            url = "https://api.x.com/2/oauth2/token"
            client_id = self._require(self.settings.x_client_id, "X_CLIENT_ID")
            data = {
                "code": code,
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": oauth_state.redirect_uri,
                "code_verifier": self.cipher.decrypt(oauth_state.code_verifier_encrypted or ""),
            }
            secret = self.settings.x_client_secret
            auth = (client_id, secret.get_secret_value()) if secret else None
        elif platform == Platform.LINKEDIN:
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._require(self.settings.linkedin_client_id, "LINKEDIN_CLIENT_ID"),
                "client_secret": self._require_secret(
                    self.settings.linkedin_client_secret, "LINKEDIN_CLIENT_SECRET"
                ),
                "redirect_uri": oauth_state.redirect_uri,
            }
            auth = None
        else:
            raise ConnectorConfigurationError(f"OAuth is not supported for {platform.value}")

        request_kwargs: dict[str, Any] = {
            "data": data,
            "headers": {"Accept": "application/json"},
        }
        if auth is not None:
            request_kwargs["auth"] = auth

        async with httpx.AsyncClient(timeout=self.settings.connector_timeout_seconds) as client:
            response = await client.post(url, **request_kwargs)
        if response.is_error:
            raise ConnectorError(
                f"OAuth token exchange failed for {platform.value}: {response.text[:500]}",
                status_code=response.status_code,
            )
        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise ConnectorError(
                f"OAuth token exchange returned no access token for {platform.value}"
            )
        return payload

    @staticmethod
    def _require(value: str | None, name: str) -> str:
        if not value:
            raise ConnectorConfigurationError(f"{name} is not configured")
        return value

    @staticmethod
    def _require_secret(value: Any, name: str) -> str:
        if value is None:
            raise ConnectorConfigurationError(f"{name} is not configured")
        return str(value.get_secret_value())
