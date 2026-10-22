from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentRun, Artifact, Batch, Benchmark, ProductProfile
from ..services.events import bus
from ..services.fact_guard import check_output
from ..services.knowledge import list_knowledge_docs
from ..services.packaging import render_label_png
from ..services.pricing import calculate_pricing
from .base import AgentName
from .engine import AgentGenerationError, _guard_allowed_numbers, generate_output
from .runtime import AgentRuntime
from .schemas import validate_output

AGENT_ORDER = (AgentName.STORY, AgentName.PACKAGING, AgentName.MARKETING, AgentName.PRICING)

AGENT_FIELD = {
    AgentName.STORY: "story_json",
    AgentName.PACKAGING: "packaging_json",
    AgentName.MARKETING: "marketing_json",
    AgentName.PRICING: "pricing_json",
}

READY_STATE = {
    AgentName.STORY: "raw",
    AgentName.PACKAGING: "story_approved",
    AgentName.MARKETING: "packaging_approved",
    AgentName.PRICING: "marketing_approved",
}


def next_agent(batch: Batch) -> AgentName | None:
    for agent in AGENT_ORDER:
        if batch.state == READY_STATE[agent]:
            return agent
    return None


def _now() -> datetime:
    return datetime.now(UTC)


async def _latest_run(
    session: AsyncSession,
    batch_id: int,
    agent: AgentName,
    status: str | None = None,
) -> AgentRun | None:
    query = select(AgentRun).where(
        AgentRun.batch_id == batch_id,
        AgentRun.agent == agent.value,
    )
    if status is not None:
        query = query.where(AgentRun.status == status)
    return await session.scalar(query.order_by(AgentRun.id.desc()))


def _guard_payload(error: AgentGenerationError) -> dict | None:
    return error.guard.as_dict() if error.guard else None


async def _store_illustration(
    session: AsyncSession,
    batch: Batch,
    run: AgentRun,
    content: dict,
    runtime: AgentRuntime,
) -> Artifact | None:
    if runtime.image_provider_name == "mock":
        return None
    prompt = str(content.get("ip_image_prompt") or "").strip()
    if not prompt:
        return None

    path = runtime.artifact_dir / f"batch-{batch.id}" / f"illustration-{run.id}.png"
    payload: dict = {"prompt": prompt, "model": runtime.settings.image_model}
    file_path: str | None = None
    try:
        png = await runtime.image.generate(prompt, width=768, height=1024)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
        payload["demo"] = False
        file_path = str(path)
    except Exception as exc:  # noqa: BLE001 - 生图失败不应阻塞包装审核
        payload.update({"demo": True, "error": str(exc)[:300]})

    artifact = Artifact(
        batch_id=batch.id,
        agent_run_id=run.id,
        kind="illustration",
        content_json=payload,
        file_path=file_path,
        approved_at=_now(),
    )
    session.add(artifact)
    return artifact


async def run_agent(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
    runtime: AgentRuntime,
    note: str | None = None,
) -> AgentRun:
    review_state = f"{agent.value}_review"
    if batch.state == review_state:
        previous = await _latest_run(session, batch.id, agent, status="waiting_review")
        if previous is not None:
            previous.status = "failed"
            previous.error = "superseded by rerun"
            previous.finished_at = _now()
    elif next_agent(batch) != agent:
        raise HTTPException(status_code=409, detail=f"当前不能运行 {agent.value}")

    product = await session.get(ProductProfile, batch.product_id)
    if product is None:
        raise HTTPException(status_code=409, detail="产品档案缺失")

    batch.state = f"{agent.value}_running"
    batch.current_station = agent.value
    run = AgentRun(
        batch_id=batch.id,
        agent=agent.value,
        status="running",
        input_json={
            "batch_code": batch.code,
            "product": product.slug,
            "note": note,
            "provider": runtime.provider_name,
        },
        note=note,
        started_at=_now(),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    await bus.publish(
        "agent.started", {"batch_id": batch.id, "agent": agent.value, "run_id": run.id}
    )
    await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})

    try:
        result = await generate_output(session, runtime, agent, product, batch, note)
    except AgentGenerationError as exc:
        run.status = "failed"
        run.error = str(exc)[:2000]
        run.guard_json = _guard_payload(exc)
        run.output_json = exc.output
        run.finished_at = _now()
        batch.state = READY_STATE[agent]
        await session.commit()
        await session.refresh(run)
        detail = str(exc)
        if exc.guard and exc.guard.errors:
            detail = f"{detail}：{exc.guard.errors[0].message}"
        await bus.publish(
            "agent.failed",
            {"batch_id": batch.id, "agent": agent.value, "run_id": run.id, "error": detail},
        )
        await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})
        raise HTTPException(status_code=502, detail=detail) from exc

    run.status = "waiting_review"
    run.output_json = result.output
    run.guard_json = result.guard.as_dict()
    run.model = result.model
    run.tokens = result.tokens
    run.finished_at = _now()
    setattr(batch, AGENT_FIELD[agent], result.output)
    batch.state = review_state
    await session.commit()
    await session.refresh(run)
    await session.refresh(batch)
    await bus.publish(
        "agent.completed",
        {
            "batch_id": batch.id,
            "agent": agent.value,
            "run_id": run.id,
            "status": run.status,
            "demo": result.demo,
            "warnings": len(result.guard.warnings),
        },
    )
    await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})

    if runtime.settings.auto_approve:
        await approve_agent(session, batch, agent, runtime)
        await session.refresh(run)
    return run


async def _validate_review_content(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
    content: dict,
    *,
    public_base_url: str,
    trace_code: str | None = None,
) -> tuple[dict, dict]:
    product = await session.get(ProductProfile, batch.product_id)
    if product is None:
        raise HTTPException(status_code=409, detail="产品档案缺失")
    docs = await list_knowledge_docs(session, product.id)
    try:
        model = validate_output(agent, content)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"产出不符合 Schema：{str(exc)[:500]}",
        ) from exc

    data = model.model_dump(mode="json")
    if agent == AgentName.PRICING:
        # 人工可以改解释，但价格、成本、毛利必须由服务端重算。
        result = await session.execute(
            select(Benchmark).where(Benchmark.product_id == product.id).order_by(Benchmark.id)
        )
        benchmarks = list(result.scalars().all())
        if not batch.packaging_json:
            raise HTTPException(status_code=409, detail="缺少已通过的包装产出")
        recalculated = calculate_pricing(
            product,
            batch,
            batch.packaging_json,
            benchmarks,
            docs,
            public_base_url=public_base_url,
            story=batch.story_json,
            trace_code=trace_code,
        )
        for key in (
            "price_ladder",
            "premium_pct",
            "formula",
            "cost_breakdown",
            "qr_payload",
            "is_demo",
        ):
            data[key] = recalculated[key]
        try:
            data = validate_output(agent, data).model_dump(mode="json")
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"重算后的定价不符合 Schema：{str(exc)[:500]}",
            ) from exc

    guard = check_output(
        data,
        docs,
        allowed_numbers=_guard_allowed_numbers(agent, product, batch, docs, data),
    )
    if not guard.passed:
        raise HTTPException(
            status_code=422,
            detail=f"事实校验未通过：{guard.errors[0].message}",
        )
    return data, guard.as_dict()


async def approve_agent(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
    runtime: AgentRuntime,
    output: dict | None = None,
) -> Artifact:
    review_state = f"{agent.value}_review"
    if batch.state != review_state:
        raise HTTPException(status_code=409, detail="当前不是待审核状态")

    run = await _latest_run(session, batch.id, agent, status="waiting_review")
    if run is None:
        raise HTTPException(status_code=409, detail="没有待审核的产出")

    content = output if output is not None else run.output_json
    if not isinstance(content, dict):
        raise HTTPException(status_code=422, detail="产出必须是 JSON 对象")

    pending_trace_code = batch.trace_code
    if agent == AgentName.PRICING and not pending_trace_code:
        pending_trace_code = f"ZT{batch.id:04d}"

    content, guard = await _validate_review_content(
        session,
        batch,
        agent,
        content,
        public_base_url=runtime.settings.public_base_url,
        trace_code=pending_trace_code,
    )
    run.guard_json = guard
    run.output_json = content
    run.status = "approved"
    setattr(batch, AGENT_FIELD[agent], content)
    batch.state = f"{agent.value}_approved"

    file_path: str | None = None
    if agent == AgentName.PACKAGING:
        product = await session.get(ProductProfile, batch.product_id)
        if product is None:
            raise HTTPException(status_code=409, detail="产品档案缺失")
        path = runtime.artifact_dir / f"batch-{batch.id}" / f"packaging-{run.id}.png"
        try:
            render_label_png(
                content,
                batch,
                product,
                path,
                public_base_url=runtime.settings.public_base_url,
            )
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"包装图生成失败：{exc}") from exc
        file_path = str(path)

    artifact = Artifact(
        batch_id=batch.id,
        agent_run_id=run.id,
        kind=agent.value,
        content_json=content,
        file_path=file_path,
        approved_at=_now(),
    )
    session.add(artifact)

    illustration: Artifact | None = None
    if agent == AgentName.PACKAGING:
        illustration = await _store_illustration(session, batch, run, content, runtime)

    if agent == AgentName.PRICING:
        batch.trace_code = pending_trace_code or batch.trace_code
        batch.state = "traced"
        batch.current_station = "trace"
        # 定价后溯源码才确定，重渲染包装图，让二维码真正指向该码。
        packaging_artifact = await session.scalar(
            select(Artifact)
            .where(Artifact.batch_id == batch.id, Artifact.kind == "packaging")
            .order_by(Artifact.id.desc())
        )
        product = await session.get(ProductProfile, batch.product_id)
        if packaging_artifact and batch.packaging_json and product:
            path = (
                runtime.artifact_dir
                / f"batch-{batch.id}"
                / f"packaging-{packaging_artifact.agent_run_id or packaging_artifact.id}-final.png"
            )
            render_label_png(
                batch.packaging_json,
                batch,
                product,
                path,
                public_base_url=runtime.settings.public_base_url,
            )
            packaging_artifact.file_path = str(path)

    await session.commit()
    await session.refresh(artifact)
    if illustration is not None:
        await session.refresh(illustration)
        await bus.publish(
            "artifact.ready",
            {"batch_id": batch.id, "agent": "illustration", "artifact_id": illustration.id},
        )
    await session.refresh(batch)
    await bus.publish(
        "artifact.ready",
        {"batch_id": batch.id, "agent": agent.value, "artifact_id": artifact.id},
    )
    await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})
    return artifact


async def reject_agent(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
    note: str | None = None,
) -> AgentRun:
    if batch.state != f"{agent.value}_review":
        raise HTTPException(status_code=409, detail="当前不是待审核状态")

    run = await _latest_run(session, batch.id, agent, status="waiting_review")
    if run is None:
        raise HTTPException(status_code=409, detail="没有待审核的产出")

    run.status = "failed"
    run.error = note or "人工驳回"
    run.finished_at = _now()
    await session.commit()
    await bus.publish(
        "agent.failed",
        {"batch_id": batch.id, "agent": agent.value, "run_id": run.id, "error": run.error},
    )
    return run
