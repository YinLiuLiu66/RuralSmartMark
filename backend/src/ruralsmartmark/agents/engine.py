from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Batch, Benchmark, KnowledgeDoc, ProductProfile
from ..services.fact_guard import GuardResult, check_output, format_guard_for_prompt
from ..services.knowledge import list_knowledge_docs
from ..services.pricing import calculate_pricing
from .base import AgentName
from .mock import run_mock_agent
from .prompts import build_agent_prompt, build_pricing_narrative_prompt, build_system_prompt
from .runtime import AgentRuntime
from .schemas import (
    OUTPUT_MODELS,
    PricingNarrative,
    validate_output,
)

_TEMPERATURE = {
    AgentName.STORY: 0.85,
    AgentName.PACKAGING: 0.7,
    AgentName.MARKETING: 0.8,
    AgentName.PRICING: 0.3,
}
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


class AgentGenerationError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        guard: GuardResult | None = None,
        output: dict[str, Any] | None = None,
        attempts: int = 0,
    ) -> None:
        super().__init__(message)
        self.guard = guard
        self.output = output
        self.attempts = attempts


@dataclass(slots=True)
class GenerationResult:
    output: dict[str, Any]
    model: str
    tokens: int
    guard: GuardResult
    attempts: int
    demo: bool
    fallback_reason: str | None


def _parse_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("模型没有返回 JSON 对象")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise TypeError("模型返回的 JSON 不是对象")
    return data


def _numbers(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            found.update(_numbers(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_numbers(item))
    elif isinstance(value, str):
        found.update(_NUMBER.findall(value))
    return found


def _allowed_numbers(
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    data: dict[str, Any] | None = None,
) -> set[str]:
    allowed = _numbers(product.specs)
    allowed.update(_NUMBER.findall(product.form))
    allowed.update(_NUMBER.findall(batch.code))
    allowed.update(_NUMBER.findall(f"{batch.quantity_kg:g}"))
    cited_ids = set()
    if data:
        for citation in data.get("cultural_evidence") or data.get("fact_refs") or []:
            if isinstance(citation, dict) and citation.get("doc_id"):
                cited_ids.add(str(citation["doc_id"]))
    selected_docs = [doc for doc in docs if doc.doc_key in cited_ids] or docs
    for doc in selected_docs:
        allowed.update(_NUMBER.findall(doc.content))
    if data:
        allowed.update(_numbers(data.get("structure") or {}))
        allowed.update(_numbers(data.get("cost_estimate") or {}))
    return allowed


def _guard_allowed_numbers(
    agent: AgentName,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    data: dict[str, Any],
) -> set[str]:
    allowed = _allowed_numbers(product, batch, docs, data)
    if agent == AgentName.PRICING:
        allowed.update(_numbers(data))
    return allowed


def _guard_summary(guard: GuardResult) -> str:
    issues = guard.errors or guard.warnings
    parts = [f"{item.rule} {item.field}: {item.message}" for item in issues[:2]]
    return "；".join(parts)[:280]


async def _benchmarks(session: AsyncSession, product_id: int) -> list[Benchmark]:
    result = await session.execute(
        select(Benchmark).where(Benchmark.product_id == product_id).order_by(Benchmark.id)
    )
    return list(result.scalars().all())


async def _mock_output(
    agent: AgentName,
    runtime: AgentRuntime,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    benchmarks: list[Benchmark],
) -> dict[str, Any]:
    return await run_mock_agent(
        agent,
        product,
        batch,
        docs,
        benchmarks,
        packaging=batch.packaging_json,
        public_base_url=runtime.settings.public_base_url,
    )


async def _validated_mock(
    agent: AgentName,
    runtime: AgentRuntime,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    benchmarks: list[Benchmark],
    *,
    fallback_reason: str | None = None,
    attempts: int = 0,
) -> GenerationResult:
    output = await _mock_output(agent, runtime, product, batch, docs, benchmarks)
    output["demo"] = True
    output["fallback_reason"] = fallback_reason
    model = validate_output(agent, output)
    data = model.model_dump(mode="json")
    guard = check_output(
        data,
        docs,
        allowed_numbers=_guard_allowed_numbers(agent, product, batch, docs, data),
    )
    if not guard.passed:
        raise AgentGenerationError(
            "mock 产出未通过事实校验",
            guard=guard,
            output=data,
            attempts=attempts,
        )
    return GenerationResult(
        output=data,
        model="mock",
        tokens=0,
        guard=guard,
        attempts=attempts,
        demo=True,
        fallback_reason=fallback_reason,
    )


async def _generate_pricing(
    session: AsyncSession,
    runtime: AgentRuntime,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    benchmarks: list[Benchmark],
) -> GenerationResult:
    if not batch.packaging_json:
        raise AgentGenerationError("定价前缺少已通过的包装产出")
    base = calculate_pricing(
        product,
        batch,
        batch.packaging_json,
        benchmarks,
        docs,
        public_base_url=runtime.settings.public_base_url,
        story=batch.story_json,
        trace_code=batch.trace_code,
    )
    base["demo"] = runtime.provider_name == "mock"

    model_name = "mock" if runtime.provider_name == "mock" else "template"
    tokens = 0
    if runtime.provider_name != "mock":
        allowed = _allowed_numbers(product, batch, docs, base)
        prompt = build_pricing_narrative_prompt(base, allowed)
        try:
            response = await runtime.llm.complete(
                build_system_prompt(product),
                prompt,
                temperature=_TEMPERATURE[AgentName.PRICING],
                json_mode=True,
            )
            model_name = response.model
            tokens = response.tokens
            narrative = PricingNarrative.model_validate(_parse_json(response.text))
            narrative_data = narrative.model_dump(mode="json")
            if _numbers(narrative_data) <= allowed:
                merged = {**base, **narrative_data, "narrative_source": "llm"}
                guard = check_output(
                    merged,
                    docs,
                    allowed_numbers=_guard_allowed_numbers(
                        AgentName.PRICING, product, batch, docs, merged
                    ),
                )
                if guard.passed:
                    validated = validate_output(AgentName.PRICING, merged)
                    return GenerationResult(
                        output=validated.model_dump(mode="json"),
                        model=model_name,
                        tokens=tokens,
                        guard=guard,
                        attempts=1,
                        demo=False,
                        fallback_reason=None,
                    )
                base["fallback_reason"] = "定价解释未通过事实校验，已使用模板解释"
            else:
                base["fallback_reason"] = "定价解释的数字与计算器不一致，已使用模板解释"
        except Exception as exc:  # noqa: BLE001 - provider failures degrade to template
            base["fallback_reason"] = f"定价解释调用失败，已使用模板解释: {str(exc)[:160]}"

    guard = check_output(
        base,
        docs,
        allowed_numbers=_guard_allowed_numbers(AgentName.PRICING, product, batch, docs, base),
    )
    validated = validate_output(AgentName.PRICING, base)
    return GenerationResult(
        output=validated.model_dump(mode="json"),
        model=model_name,
        tokens=tokens,
        guard=guard,
        attempts=1,
        demo=runtime.provider_name == "mock",
        fallback_reason=base.get("fallback_reason"),
    )


async def generate_output(
    session: AsyncSession,
    runtime: AgentRuntime,
    agent: AgentName,
    product: ProductProfile,
    batch: Batch,
    note: str | None = None,
) -> GenerationResult:
    docs = await list_knowledge_docs(session, product.id)
    if not docs:
        raise AgentGenerationError("知识库为空，请先运行 seed 写入知识库")
    benchmarks = await _benchmarks(session, product.id)

    if agent == AgentName.PRICING:
        return await _generate_pricing(session, runtime, product, batch, docs, benchmarks)

    upstream: dict[str, Any] = {}
    for name, value in (
        ("story", batch.story_json),
        ("packaging", batch.packaging_json),
        ("marketing", batch.marketing_json),
    ):
        if value:
            upstream[name] = value

    schema = OUTPUT_MODELS[agent].model_json_schema()
    attempts = 0

    if runtime.provider_name == "mock":
        return await _validated_mock(agent, runtime, product, batch, docs, benchmarks)

    feedback: str | None = None
    total_tokens = 0
    last_guard: GuardResult | None = None
    last_output: dict[str, Any] | None = None
    last_error = "模型输出未通过校验"

    for attempts in range(1, 3):
        prompt = build_agent_prompt(
            agent,
            product,
            batch,
            docs,
            upstream,
            note,
            schema,
            feedback=feedback,
        )
        try:
            response = await runtime.llm.complete(
                build_system_prompt(product),
                prompt,
                temperature=_TEMPERATURE[agent],
                json_mode=True,
            )
        except Exception as exc:  # noqa: BLE001 - provider failures degrade to mock
            last_error = f"模型调用失败: {exc}"
            break

        total_tokens += response.tokens
        try:
            data = _parse_json(response.text)
            model = validate_output(agent, data)
        except (TypeError, ValueError, ValidationError) as exc:
            last_error = f"JSON/Schema 校验失败: {str(exc)[:300]}"
            feedback = f"JSON 或字段校验失败，请按 Schema 重新输出完整 JSON：\n{str(exc)[:1600]}"
            continue

        data = model.model_dump(mode="json")
        data["demo"] = False
        data["fallback_reason"] = None
        last_output = data
        guard = check_output(
            data,
            docs,
            allowed_numbers=_guard_allowed_numbers(agent, product, batch, docs, data),
        )
        last_guard = guard
        if guard.passed:
            return GenerationResult(
                output=data,
                model=response.model,
                tokens=total_tokens,
                guard=guard,
                attempts=attempts,
                demo=bool(data.get("demo")),
                fallback_reason=data.get("fallback_reason"),
            )

        last_error = f"事实校验未通过（{_guard_summary(guard)}）"
        feedback = (
            "以下问题必须修复；引用要逐字复制知识库，不要新增未核数字：\n"
            + format_guard_for_prompt(guard)
        )

    if runtime.allow_mock_fallback:
        return await _validated_mock(
            agent,
            runtime,
            product,
            batch,
            docs,
            benchmarks,
            fallback_reason=f"{last_error}，已降级为演示稿",
            attempts=attempts,
        )

    raise AgentGenerationError(
        last_error,
        guard=last_guard,
        output=last_output,
        attempts=attempts,
    )
