from ruralsmartmark.config import get_settings
from ruralsmartmark.providers.llm import _build_request, _thinking_budget


def _settings(**updates):
    return get_settings().model_copy(update=updates)


def test_request_contains_thinking_budget_and_max_tokens():
    settings = _settings(
        openai_model="deepseek-ai/DeepSeek-V4.1-Flash",
        llm_thinking_budget=2048,
        llm_max_tokens=4096,
    )
    request = _build_request(
        settings,
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        json_mode=True,
    )

    assert request["model"] == "deepseek-ai/DeepSeek-V4.1-Flash"
    assert request["max_tokens"] == 4096
    assert request["extra_body"] == {"thinking_budget": 2048}
    assert request["response_format"] == {"type": "json_object"}


def test_thinking_budget_can_be_disabled_and_is_clamped():
    assert _thinking_budget(_settings(llm_thinking_budget=0)) is None
    assert _thinking_budget(_settings(llm_thinking_budget=100)) == 128
    assert _thinking_budget(_settings(llm_thinking_budget=99999)) == 32768

    request = _build_request(
        _settings(llm_thinking_budget=0),
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        json_mode=False,
    )
    assert "extra_body" not in request
    assert "response_format" not in request
