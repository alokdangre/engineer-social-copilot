from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TypeVar

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.config import Settings, get_settings
from social_manager.db.session import database
from social_manager.domain.enums import LLMProvider
from social_manager.services.llm_credentials import (
    LLMCredentialService,
    ResolvedLLMCredential,
)

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)
logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ModelRuntime:
    api_key: str
    base_url: str | None
    reasoning_model: str
    extraction_model: str
    embedding_model: str


class ModelGateway:
    """Provider boundary for structured generation and optional embeddings."""

    def __init__(
        self,
        settings: Settings | None = None,
        credential_service: LLMCredentialService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.credential_service = credential_service or LLMCredentialService(self.settings)

    async def generate(
        self,
        schema: type[StructuredModel],
        *,
        system_prompt: str,
        payload: dict[str, object],
        fallback: StructuredModel,
        role: str = "reasoning",
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> StructuredModel:
        model_name: str | None = None
        try:
            runtime = await self._runtime(user_id=user_id, session=session)
            if runtime is None:
                return fallback

            model_name = (
                runtime.extraction_model if role == "extraction" else runtime.reasoning_model
            )
            model_kwargs: dict[str, Any] = {
                "model": model_name,
                "api_key": runtime.api_key,
                "temperature": 0,
            }
            if runtime.base_url:
                model_kwargs["base_url"] = runtime.base_url

            model = ChatOpenAI(**model_kwargs)
            structured_model = model.with_structured_output(schema, method="json_schema")
            response = await structured_model.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=json.dumps(payload, default=str, ensure_ascii=False)),
                ]
            )
            if isinstance(response, schema):
                return response
            return schema.model_validate(response)
        except Exception:
            logger.exception(
                "structured_model_call_failed",
                model=model_name,
                schema=schema.__name__,
                user_id=user_id,
            )
            if not self.settings.model_fallback_enabled:
                raise
            return fallback

    async def embed(
        self,
        text: str,
        *,
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> list[float] | None:
        if not text.strip():
            return None
        model_name: str | None = None
        try:
            runtime = await self._runtime(user_id=user_id, session=session)
            if runtime is None:
                return None

            model_name = runtime.embedding_model
            embedding_kwargs: dict[str, Any] = {
                "model": model_name,
                "api_key": runtime.api_key,
            }
            if runtime.base_url:
                embedding_kwargs["base_url"] = runtime.base_url

            client = OpenAIEmbeddings(**embedding_kwargs)
            return await client.aembed_query(text)
        except Exception:
            logger.exception(
                "embedding_call_failed",
                model=model_name,
                user_id=user_id,
            )
            if not self.settings.model_fallback_enabled:
                raise
            return None

    async def _runtime(
        self,
        *,
        user_id: str | None,
        session: AsyncSession | None,
    ) -> ModelRuntime | None:
        if user_id is not None:
            credential = await self._resolve_user_credential(user_id, session)
            if credential is None:
                return None
            return self._runtime_for_credential(credential)

        provider = LLMProvider(self.settings.llm_provider)
        key = (
            self.settings.gemini_api_key
            if provider is LLMProvider.GEMINI
            else self.settings.openai_api_key
        )
        if key is None:
            return None
        return self._runtime_for_credential(
            ResolvedLLMCredential(provider=provider, api_key=key.get_secret_value())
        )

    async def _resolve_user_credential(
        self,
        user_id: str,
        session: AsyncSession | None,
    ) -> ResolvedLLMCredential | None:
        if session is not None:
            return await self.credential_service.resolve(session, user_id)
        async with database.session_factory() as credential_session:
            return await self.credential_service.resolve(credential_session, user_id)

    def _runtime_for_credential(
        self,
        credential: ResolvedLLMCredential,
    ) -> ModelRuntime:
        if credential.provider is LLMProvider.GEMINI:
            return ModelRuntime(
                api_key=credential.api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                reasoning_model=self.settings.reasoning_model,
                extraction_model=self.settings.extraction_model,
                embedding_model=self.settings.embedding_model,
            )
        return ModelRuntime(
            api_key=credential.api_key,
            base_url=self.settings.openai_base_url,
            reasoning_model=self.settings.openai_reasoning_model,
            extraction_model=self.settings.openai_extraction_model,
            embedding_model=self.settings.openai_embedding_model,
        )
