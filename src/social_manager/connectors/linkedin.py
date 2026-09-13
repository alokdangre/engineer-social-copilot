from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from social_manager.connectors.base import (
    BaseConnector,
    ExternalContent,
    ExternalIdentity,
    SyncBatch,
)
from social_manager.domain.enums import ContentType, Platform


class LinkedInConnector(BaseConnector):
    platform = Platform.LINKEDIN

    @property
    def base_url(self) -> str:
        return "https://api.linkedin.com"

    @property
    def headers(self) -> dict[str, str]:
        return {
            **super().headers,
            "LinkedIn-Version": "202608",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def get_identity(self) -> ExternalIdentity:
        profile = await self.request("GET", "/v2/userinfo")
        return ExternalIdentity(
            external_user_id=str(profile["sub"]),
            username=None,
            display_name=profile.get("name"),
            profile_url=None,
            metadata={
                "given_name": profile.get("given_name"),
                "family_name": profile.get("family_name"),
                "locale": profile.get("locale"),
                "picture": profile.get("picture"),
            },
        )

    async def sync_own_content(self, cursor: str | None = None) -> SyncBatch:
        identity = await self.get_identity()
        params: dict[str, Any] = {
            "author": f"urn:li:person:{identity.external_user_id}",
            "q": "author",
            "count": 50,
            "sortBy": "LAST_MODIFIED",
        }
        if cursor:
            params["start"] = cursor
        try:
            response = await self.request("GET", "/rest/posts", params=params)
        except Exception as exc:
            return SyncBatch(
                identity=identity,
                warnings=[
                    "LinkedIn profile connected, but member post access is unavailable for the "
                    f"approved application permissions: {exc}"
                ],
            )
        elements = response.get("elements", [])
        items = [self._post_item(item, identity) for item in elements]
        paging = response.get("paging", {})
        start = int(paging.get("start", 0))
        count = int(paging.get("count", len(elements)))
        total = int(paging.get("total", len(elements)))
        next_cursor = str(start + count) if start + count < total else None
        return SyncBatch(identity=identity, content=items, cursor=next_cursor)

    def _post_item(self, post: dict[str, Any], identity: ExternalIdentity) -> ExternalContent:
        commentary = post.get("commentary")
        if isinstance(commentary, dict):
            commentary = commentary.get("text")
        published_at = post.get("publishedAt") or post.get("createdAt")
        post_id = str(post.get("id"))
        return ExternalContent(
            platform=self.platform,
            external_id=f"post:{post_id}",
            content_type=ContentType.POST,
            author_external_id=identity.external_user_id,
            author_name=identity.display_name,
            body=commentary if isinstance(commentary, str) else None,
            url=None,
            published_at=(
                datetime.fromtimestamp(int(published_at) / 1000, UTC) if published_at else None
            ),
            metrics={},
            normalized_data={
                "lifecycle_state": post.get("lifecycleState"),
                "visibility": post.get("visibility"),
                "content": post.get("content"),
            },
            is_own=True,
        )
