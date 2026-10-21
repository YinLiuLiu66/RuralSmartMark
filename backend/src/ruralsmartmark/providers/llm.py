from dataclasses import dataclass
from typing import Protocol

from ..config import Settings


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str


class LLMProvider(Protocol):
    name: str

    async def complete(
        self, system: str, user: str, *, temperature: float = 0.7
    ) -> LLMResponse: ...


class MockLLMProvider:
    name = "mock"

    async def complete(
        self, system: str, user: str, *, temperature: float = 0.7
    ) -> LLMResponse:
        return LLMResponse(text=f"[mock] {user[:120]}", model="mock")


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.openai_model

    async def complete(
        self, system: str, user: str, *, temperature: float = 0.7
    ) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        return LLMResponse(text=text, model=self._model)


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.openai_api_key:
        return OpenAIProvider(settings)
    return MockLLMProvider()
