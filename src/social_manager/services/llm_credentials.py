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

    async def upsert(
        self,
        session: AsyncSession,
        user_id: str,
        data: LLMCredentialInput,
    ) -> LLMCredentialRead:
        api_key = data.api_key.get_secret_value().strip()
        credential = await self._get(session, user_id)
        if credential is None:
            credential = UserLLMCredential(user_id=user_id)
            session.add(credential)

        credential.provider = data.provider.value
        credential.encrypted_api_key = self.cipher.encrypt(api_key)
        credential.key_hint = api_key[-4:]
        await session.commit()
        await session.refresh(credential)
        return await self.describe(session, user_id)

    async def resolve(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> ResolvedLLMCredential | None:
        credential = await self._get(session, user_id)
        if credential is None:
            return None
        return ResolvedLLMCredential(
            provider=LLMProvider(credential.provider),
            api_key=self.cipher.decrypt(credential.encrypted_api_key),
        )

    async def delete(self, session: AsyncSession, user_id: str) -> None:
        credential = await self._get(session, user_id)
        if credential is None:
            return
        await session.delete(credential)
        await session.commit()

    @staticmethod
    async def _get(
        session: AsyncSession,
        user_id: str,
    ) -> UserLLMCredential | None:
        result = await session.scalars(
            select(UserLLMCredential).where(UserLLMCredential.user_id == user_id)
        )
        return result.one_or_none()
