from __future__ import annotations

from datetime import datetime
from typing import Any

from social_manager.connectors.base import (
    BaseConnector,
    ExternalContent,
    ExternalIdentity,
    SyncBatch,
)
from social_manager.domain.enums import ContentType, Platform


class XConnector(BaseConnector):
    platform = Platform.X

    @property
    def base_url(self) -> str:
        return "https://api.x.com"

    async def get_identity(self) -> ExternalIdentity:
        response = await self.request(
            "GET",
            "/2/users/me",
            params={"user.fields": "created_at,description,location,public_metrics,verified"},
        )
        profile = response["data"]
        return ExternalIdentity(
            external_user_id=str(profile["id"]),
            username=profile.get("username"),
            display_name=profile.get("name"),
            profile_url=(
                f"https://x.com/{profile['username']}" if profile.get("username") else None
            ),
            metadata={
                "description": profile.get("description"),
                "location": profile.get("location"),
                "verified": profile.get("verified"),
                "public_metrics": profile.get("public_metrics", {}),
            },
        )

    async def sync_own_content(self, cursor: str | None = None) -> SyncBatch:
        identity = await self.get_identity()
        params: dict[str, Any] = {
            "max_results": 100,
            "tweet.fields": (
                "created_at,conversation_id,public_metrics,referenced_tweets,reply_settings"
            ),
            "exclude": "retweets",
        }
        if cursor:
            params["pagination_token"] = cursor
        endpoint = f"/2/users/{identity.external_user_id}/tweets"
        response = await self.request("GET", endpoint, params=params)
        items = [self._post_item(item, identity) for item in response.get("data", [])]
        return SyncBatch(
            identity=identity,
            content=items,
            cursor=response.get("meta", {}).get("next_token"),
        )

    def _post_item(self, post: dict[str, Any], identity: ExternalIdentity) -> ExternalContent:
        references = post.get("referenced_tweets", [])
        content_type = ContentType.POST
        if any(item.get("type") == "replied_to" for item in references):
            content_type = ContentType.REPLY
        elif any(item.get("type") == "quoted" for item in references):
            content_type = ContentType.REPOST
        return ExternalContent(
            platform=self.platform,
            external_id=f"post:{post['id']}",
            content_type=content_type,
            author_external_id=identity.external_user_id,
            author_name=identity.username,
            body=post.get("text"),
            url=(
                f"https://x.com/{identity.username}/status/{post['id']}"
                if identity.username
                else None
            ),
            published_at=self._parse_datetime(post.get("created_at")),
            metrics=post.get("public_metrics", {}),
            normalized_data={
                "conversation_id": post.get("conversation_id"),
                "referenced_tweets": references,
                "reply_settings": post.get("reply_settings"),
            },
            is_own=True,
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
