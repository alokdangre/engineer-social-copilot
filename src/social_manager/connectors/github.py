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


class GitHubConnector(BaseConnector):
    platform = Platform.GITHUB

    @property
    def base_url(self) -> str:
        return "https://api.github.com"

    @property
    def headers(self) -> dict[str, str]:
        return {
            **super().headers,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "social-media-manager",
        }

    async def get_identity(self) -> ExternalIdentity:
        profile = await self.request("GET", "/user")
        return ExternalIdentity(
            external_user_id=str(profile["id"]),
            username=profile.get("login"),
            display_name=profile.get("name"),
            profile_url=profile.get("html_url"),
            metadata={
                "bio": profile.get("bio"),
                "company": profile.get("company"),
                "public_repos": profile.get("public_repos"),
                "followers": profile.get("followers"),
                "following": profile.get("following"),
            },
        )

    async def sync_own_content(self, cursor: str | None = None) -> SyncBatch:
        identity = await self.get_identity()
        page = int(cursor or "1")
        repositories = await self.request(
            "GET",
            "/user/repos",
            params={
                "affiliation": "owner,collaborator,organization_member",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
        )
        raw_items = (
            repositories if isinstance(repositories, list) else repositories.get("items", [])
        )
        content = [self._repository_item(item, identity) for item in raw_items]
        next_cursor = str(page + 1) if len(raw_items) == 100 else None
        return SyncBatch(identity=identity, content=content, cursor=next_cursor)

    def _repository_item(
        self, repository: dict[str, Any], identity: ExternalIdentity
    ) -> ExternalContent:
        owner = repository.get("owner") or {}
        return ExternalContent(
            platform=self.platform,
            external_id=f"repo:{repository['id']}",
            content_type=ContentType.REPOSITORY,
            author_external_id=str(owner.get("id") or identity.external_user_id),
            author_name=owner.get("login") or identity.username,
            body=repository.get("description"),
            url=repository.get("html_url"),
            published_at=self._parse_datetime(repository.get("created_at")),
            metrics={
                "stars": repository.get("stargazers_count", 0),
                "forks": repository.get("forks_count", 0),
                "watchers": repository.get("watchers_count", 0),
                "open_issues": repository.get("open_issues_count", 0),
            },
            normalized_data={
                "name": repository.get("name"),
                "full_name": repository.get("full_name"),
                "language": repository.get("language"),
                "topics": repository.get("topics", []),
                "fork": repository.get("fork", False),
                "private": repository.get("private", False),
                "archived": repository.get("archived", False),
                "default_branch": repository.get("default_branch"),
                "updated_at": repository.get("updated_at"),
                "pushed_at": repository.get("pushed_at"),
            },
            is_own=owner.get("id") == int(identity.external_user_id),
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
