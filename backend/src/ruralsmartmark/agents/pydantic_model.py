from __future__ import annotations

from typing import Any

from ..config import Settings


def build_pydantic_model(settings: Settings) -> Any:
    """Chat Completions model for the controller/research agents (not Responses API)."""
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    )
    return OpenAIChatModel(
        settings.openai_model,
        provider=OpenAIProvider(openai_client=client),
    )


def build_model_settings(
    settings: Settings,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> Any:
    """SiliconFlow 的 thinking_budget 走 extra_body；不配置时模型可能不返回思维链。"""
    from pydantic_ai.settings import ModelSettings

    extra_body: dict[str, int] = {}
    if settings.llm_thinking_budget > 0:
        extra_body["thinking_budget"] = max(
            128, min(settings.llm_thinking_budget, 32768)
        )
    values: dict[str, Any] = {}
    if max_tokens or settings.llm_max_tokens:
        values["max_tokens"] = max_tokens or settings.llm_max_tokens
    if temperature is not None:
        values["temperature"] = temperature
    if extra_body:
        values["extra_body"] = extra_body
    return ModelSettings(**values)
