from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from social_manager.config import Settings, get_settings
from social_manager.domain.enums import ContentType, Platform


class ConnectorError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class ExternalIdentity(BaseModel):
    external_user_id: str
    username: str | None = None
    display_name: str | None = None
    profile_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalContent(BaseModel):
    platform: Platform
    external_id: str
    content_type: ContentType
    author_external_id: str | None = None
    author_name: str | None = None
    body: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    normalized_data: dict[str, Any] = Field(default_factory=dict)
    is_own: bool = False


class SyncBatch(BaseModel):
    identity: ExternalIdentity | None = None
    content: list[ExternalContent] = Field(default_factory=list)
    cursor: str | None = None
    warnings: list[str] = Field(default_factory=list)


class BaseConnector(ABC):
    platform: Platform

    def __init__(
        self,
        access_token: str,
        *,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.access_token = access_token
        self.settings = settings or get_settings()
        self._external_client = client

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        owns_client = self._external_client is None
        client = self._external_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.settings.connector_timeout_seconds,
            headers=self.headers,
        )
        try:
            for attempt in range(self.settings.connector_max_retries):
                try:
                    response = await client.request(method, path, params=params)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt + 1 >= self.settings.connector_max_retries:
                        raise ConnectorError(str(exc), retryable=True) from exc
                    await asyncio.sleep(0.25 * (2**attempt))
                    continue
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt + 1 < self.settings.connector_max_retries:
                        await asyncio.sleep(0.25 * (2**attempt))
                        continue
                    raise ConnectorError(
                        f"{self.platform.value} request failed with {response.status_code}",
                        retryable=True,
                        status_code=response.status_code,
                    )
                if response.is_error:
                    detail = response.text[:500]
                    raise ConnectorError(
                        f"{self.platform.value} request failed: {detail}",
                        status_code=response.status_code,
                    )
                body = response.json()
                if not isinstance(body, (dict, list)):
                    raise ConnectorError(f"{self.platform.value} returned an unexpected response")
                return body
        finally:
            if owns_client:
                await client.aclose()
        raise ConnectorError(f"{self.platform.value} request did not complete", retryable=True)

    @abstractmethod
    async def get_identity(self) -> ExternalIdentity:
        raise NotImplementedError

    @abstractmethod
    async def sync_own_content(self, cursor: str | None = None) -> SyncBatch:
        raise NotImplementedError
