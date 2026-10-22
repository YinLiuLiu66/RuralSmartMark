from dataclasses import dataclass
from typing import Protocol

from ..config import Settings


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    tokens: int = 0


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse: ...


class MockLLMProvider:
    name = "mock"

    async def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        return LLMResponse(text="{}", model="mock", tokens=0)


def _thinking_budget(settings: Settings) -> int | None:
    """SiliconFlow accepts 128–32768; 0 disables the parameter."""
    if settings.llm_thinking_budget <= 0:
        return None
    return max(128, min(settings.llm_thinking_budget, 32768))


def _build_request(
    settings: Settings,
    messages: list[dict[str, str]],
    *,
    temperature: float,
    json_mode: bool,
) -> dict:
    request: dict = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": temperature,
    }
    if settings.llm_max_tokens > 0:
        request["max_tokens"] = settings.llm_max_tokens

    extra_body: dict = {}
    budget = _thinking_budget(settings)
    if budget is not None:
        extra_body["thinking_budget"] = budget
    if extra_body:
        request["extra_body"] = extra_body

    if json_mode:
        request["response_format"] = {"type": "json_object"}
    return request


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )
        self._settings = settings
        self._model = settings.openai_model

    async def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        request = _build_request(
            self._settings,
            messages,
            temperature=temperature,
            json_mode=json_mode,
        )

        try:
            response = await self._client.chat.completions.create(**request)
        except Exception as exc:
            # Some OpenAI-compatible gateways do not accept response_format.
            # Retry once without it only for a 400-class rejection.
            if not json_mode or getattr(exc, "status_code", None) != 400:
                raise
            request.pop("response_format", None)
            response = await self._client.chat.completions.create(**request)

        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        tokens = int(getattr(usage, "total_tokens", 0) or 0)
        return LLMResponse(text=text, model=self._model, tokens=tokens)


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.openai_api_key:
        return OpenAIProvider(settings)
    return MockLLMProvider()
