"""LLM 接入封装（decisions #6/#21/#23）：手写编排，不引框架。

空 key 不在这里兜底——service 层据此走 mock，保证测试与断网演示不联网。
"""

from openai import AsyncOpenAI

from ruralsmartmark.config import settings

_client: AsyncOpenAI | None = None


class LLMError(RuntimeError):
    """模型调用失败（超时 / 空返回 / 端点错误），由任务层落 failed。"""


def is_configured() -> bool:
    return bool(settings.openai_api_key)


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
            timeout=90.0,
            max_retries=1,
        )
    return _client


async def complete(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1600,
    temperature: float = 0.8,
) -> str:
    """单轮补全，只取正文；思维链字段（若有）一律丢弃（#22/#23）。"""
    if not is_configured():
        raise LLMError("未配置 OPENAI_API_KEY")

    try:
        response = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:  # noqa: BLE001 — 端点异常统一映射为任务失败
        raise LLMError(f"模型调用失败：{e}") from e

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise LLMError("模型返回空内容")
    return content
