from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.config import Settings, get_settings
from social_manager.db.models import UserLLMCredential
from social_manager.domain.enums import LLMProvider
from social_manager.domain.schemas import LLMCredentialInput, LLMCredentialRead
from social_manager.security import TokenCipher


@dataclass(frozen=True)
class ResolvedLLMCredential:
    provider: LLMProvider
    api_key: str


class LLMCredentialService:
    def __init__(
        self,
        settings: Settings | None = None,
        cipher: TokenCipher | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.cipher = cipher or TokenCipher(self.settings)

    async def describe(self, session: AsyncSession, user_id: str) -> LLMCredentialRead:
        credential = await self._get(session, user_id)
        if credential is None:
            return LLMCredentialRead(configured=False)
        return LLMCredentialRead(
            configured=True,
            provider=LLMProvider(credential.provider),
            key_hint=credential.key_hint,
            updated_at=credential.updated_at,
        )

    async def test? no
