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
