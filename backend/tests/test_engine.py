import json

import pytest
from sqlalchemy import select

from ruralsmartmark.agents.base import AgentName
from ruralsmartmark.agents.engine import AgentGenerationError, generate_output
from ruralsmartmark.agents.mock import run_mock_agent
from ruralsmartmark.agents.runtime import AgentRuntime
from ruralsmartmark.config import get_settings
from ruralsmartmark.models import Batch, Benchmark, ProductProfile
from ruralsmartmark.providers.llm import LLMResponse
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.knowledge import list_knowledge_docs


class FakeLLM:
    name = "fake"

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls = 0

    async def complete(self, system, user, *, temperature=0.7, json_mode=False):
        self.calls += 1
        text = self.responses.pop(0) if self.responses else "{}"
        return LLMResponse(text=text, model="fake-model", tokens=12)


async def _context(session):
    await seed_demo(session)
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "zhaotong-ugly-apple")
    )
    batch = await session.scalar(select(Batch).where(Batch.code == "ZT-2026-001"))
    benchmarks = list(
        (await session.execute(select(Benchmark).where(Benchmark.product_id == product.id)))
        .scalars()
        .all()
    )
    docs = await list_knowledge_docs(session, product.id)
    return product, batch, benchmarks, docs


async def _valid_story(product, batch, docs, benchmarks) -> dict:
    data = await run_mock_agent(AgentName.STORY, product, batch, docs, benchmarks)
    data["demo"] = False
    return data


async def test_schema_retry_then_success(session, tmp_path):
    product, batch, benchmarks, docs = await _context(session)
    valid = await _valid_story(product, batch, docs, benchmarks)
    fake = FakeLLM(["not json at all", json.dumps(valid, ensure_ascii=False)])
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=fake,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )

    result = await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert fake.calls == 2
    assert result.attempts == 2
    assert result.model == "fake-model"
    assert result.tokens == 24
    assert result.output["ip_name"] == "山风守园人"
    assert result.guard.passed


async def test_fact_guard_retry_then_success(session, tmp_path):
    product, batch, benchmarks, docs = await _context(session)
    valid = await _valid_story(product, batch, docs, benchmarks)
    unsafe = {**valid, "story_long": valid["story_long"] + "这是有机认证苹果。"}
    fake = FakeLLM(
        [
            json.dumps(unsafe, ensure_ascii=False),
            json.dumps(valid, ensure_ascii=False),
        ]
    )
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=fake,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )

    result = await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert fake.calls == 2
    assert result.guard.passed
    assert "有机" not in result.output["story_long"]


async def test_guard_failure_reason_keeps_rule(session, tmp_path):
    product, batch, benchmarks, docs = await _context(session)
    valid = await _valid_story(product, batch, docs, benchmarks)
    unsafe = json.dumps(
        {**valid, "story_long": valid["story_long"] + "这是有机认证苹果。"},
        ensure_ascii=False,
    )
    fake = FakeLLM([unsafe, unsafe])
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=fake,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )

    result = await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert result.demo is True
    assert "COMP-02" in (result.fallback_reason or "")


async def test_invalid_output_falls_back_to_mock(session, tmp_path):
    product, batch, _benchmarks, _docs = await _context(session)
    fake = FakeLLM(['{"ip_name": "太短"}', '{"ip_name": "仍然太短"}'])
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=fake,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )

    result = await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert result.demo is True
    assert result.model == "mock"
    assert result.fallback_reason
    assert result.output["ip_name"] == "山风守园人"
    assert result.guard.passed


async def test_invalid_output_without_fallback_raises(session, tmp_path):
    product, batch, _benchmarks, _docs = await _context(session)
    fake = FakeLLM(['{"ip_name": "太短"}', '{"ip_name": "仍然太短"}'])
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=fake,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=False,
    )

    with pytest.raises(AgentGenerationError) as error:
        await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert "JSON/Schema" in str(error.value)
    assert error.value.attempts == 2


class FailingLLM:
    name = "fake"

    async def complete(self, system, user, *, temperature=0.7, json_mode=False):
        raise RuntimeError("Request timed out.")


async def test_provider_error_falls_back_to_mock(session, tmp_path):
    product, batch, _benchmarks, _docs = await _context(session)
    runtime = AgentRuntime(
        settings=get_settings(),
        llm=FailingLLM(),
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )

    result = await generate_output(session, runtime, AgentName.STORY, product, batch)

    assert result.demo is True
    assert result.model == "mock"
    assert "timed out" in (result.fallback_reason or "")
