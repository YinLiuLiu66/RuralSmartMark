from types import SimpleNamespace

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse

from ruralsmartmark.agents.controller import (
    SUMMARY_TAG,
    _build_chat_messages,
    _estimate_tokens,
    _prepare_history,
)
from ruralsmartmark.models import ControllerSession


def _settings(**overrides):
    values = {
        "controller_context_tokens": 1_024_000,
        "controller_compress_ratio": 0.8,
        "llm_compress_model": "test/compressor",
        "llm_timeout_seconds": 10,
        "openai_api_key": "",
        "openai_base_url": "https://example.invalid/v1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _runtime(settings):
    return SimpleNamespace(settings=settings)


async def test_estimate_tokens_counts_cjk_heavier_than_ascii():
    cjk = _estimate_tokens("汉" * 100)
    ascii_text = _estimate_tokens("a" * 100)
    assert cjk > 60
    assert ascii_text < 40
    assert cjk > ascii_text * 2


async def test_build_chat_messages_maps_roles_and_summary_first():
    rows = [
        (1, "user", "你好"),
        (2, "assistant", "我在"),
        (3, "user", "开批次"),
    ]
    messages = _build_chat_messages("旧档案", rows)

    assert len(messages) == 4
    first = messages[0]
    assert isinstance(first, ModelRequest)
    assert SUMMARY_TAG in first.parts[0].content
    assert "旧档案" in first.parts[0].content
    assert isinstance(messages[1], ModelRequest)
    assert isinstance(messages[2], ModelResponse)
    assert isinstance(messages[3], ModelRequest)


async def test_prepare_history_below_threshold_keeps_all_rows(session, monkeypatch):
    async def _fail(*_args, **_kwargs):
        raise AssertionError("未到阈值不应调用压缩")

    monkeypatch.setattr("ruralsmartmark.agents.controller.compress_history", _fail)
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(item)
    rows = [(1, "user", "你好"), (2, "assistant", "我在")]

    messages = await _prepare_history(session, item, _runtime(_settings()), rows)

    assert len(messages) == 2
    assert item.summary_json is None


async def test_prepare_history_compresses_and_persists(session, monkeypatch):
    async def _compress(_settings, _system, _transcript):
        assert "开场" in _transcript
        return "- 任务：删掉旧批次并开新批次"

    monkeypatch.setattr(
        "ruralsmartmark.agents.controller.compress_history", _compress
    )
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(item)
    rows = [
        (1, "user", "开场" * 60),
        (2, "assistant", "好的" * 60),
        (3, "user", "那删掉吧" * 60),
    ]

    messages = await _prepare_history(
        session, item, _runtime(_settings(controller_context_tokens=100)), rows
    )

    assert len(messages) == 1
    assert isinstance(messages[0], ModelRequest)
    content = messages[0].parts[0].content
    assert SUMMARY_TAG in content
    assert "删掉旧批次并开新批次" in content
    assert item.summary_json == {"text": "- 任务：删掉旧批次并开新批次", "upto_message_id": 3}


async def test_prepare_history_compression_failure_truncates_half(session, monkeypatch):
    async def _boom(*_args, **_kwargs):
        raise RuntimeError("compressor down")

    monkeypatch.setattr(
        "ruralsmartmark.agents.controller.compress_history", _boom
    )
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(item)
    rows = [
        (1, "user", "最旧一" * 60),
        (2, "assistant", "第二旧" * 60),
        (3, "user", "第三条" * 60),
        (4, "assistant", "最新条" * 60),
    ]

    messages = await _prepare_history(
        session, item, _runtime(_settings(controller_context_tokens=100)), rows
    )

    assert len(messages) == 2
    contents = [m.parts[0].content for m in messages]
    assert "第三条" in contents[0]
    assert "最新条" in contents[1]
    assert item.summary_json is None  # 兜底不入库，下一轮再试压缩


async def test_prepare_history_skips_rows_covered_by_existing_summary(
    session, monkeypatch
):
    async def _fail(*_args, **_kwargs):
        raise AssertionError("摘要覆盖后剩余消息很小，不应触发压缩")

    monkeypatch.setattr("ruralsmartmark.agents.controller.compress_history", _fail)
    item = ControllerSession(
        summary_json={"text": "旧摘要内容", "upto_message_id": 2}
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    rows = [
        (1, "user", "已被摘要覆盖" * 100),
        (2, "assistant", "同样被覆盖" * 100),
        (3, "user", "新消息"),
    ]

    messages = await _prepare_history(session, item, _runtime(_settings()), rows)

    assert len(messages) == 2  # 摘要一条 + 未覆盖的新消息
    assert SUMMARY_TAG in messages[0].parts[0].content
    assert messages[1].parts[0].content == "新消息"


@pytest.mark.parametrize(
    ("text", "minimum"), [("汉" * 10, 5), ("a" * 40, 5)]
)
async def test_estimate_tokens_is_positive(text, minimum):
    assert _estimate_tokens(text) >= minimum
