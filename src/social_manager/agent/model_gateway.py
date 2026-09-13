from __future__ import annotations

import json
from typing import Any, TypeVar

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from social_manager.config import Settings, get_settings

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)
logger = structlog.get_logger(__name__)


class ModelGateway:
    """Provider boundary for structured generation and optional embeddings."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(
        self,
        schema: type[StructuredModel],
        *,
        system_prompt: str,
        payload: dict[str, object],
        fallback: StructuredModel,
        role: str = "reasoning",
    ) -> StructuredModel:
        api_key = self.settings.active_llm_api_key
        if api_key is None:
            return fallback

        model_name = (
            self.settings.extraction_model
            if role == "extraction"
            else self.settings.reasoning_model
        )
        base_url = self.settings.active_llm_base_url
        model_kwargs: dict[str, Any] = {
            "model": model_name,
            "api_key": api_key.get_secret_value(),
            "temperature": 0,
        }
        if base_url:
            model_kwargs["base_url"] = base_url

        model = ChatOpenAI(**model_kwargs)
        structured_model = model.with_structured_output(schema, method="json_schema")
        try:
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
            )
            if not self.settings.model_fallback_enabled:
                raise
            return fallback

    async def embed(self, text: str) -> list[float] | None:
        api_key = self.settings.active_llm_api_key
        if api_key is None or not text.strip():
            return None
        base_url = self.settings.active_llm_base_url
        embedding_kwargs: dict[str, Any] = {
            "model": self.settings.embedding_model,
            "api_key": api_key.get_secret_value(),
        }
        if base_url:
            embedding_kwargs["base_url"] = base_url

        client = OpenAIEmbeddings(**embedding_kwargs)
        try:
            return await client.aembed_query(text)
        except Exception:
            logger.exception("embedding_call_failed")
            if not self.settings.model_fallback_enabled:
                raise
            return None
