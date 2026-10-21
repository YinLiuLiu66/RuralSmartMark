from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentRun, Artifact, Batch, ProductProfile
from ..services.events import bus
from .base import AgentName
from .mock import run_mock_agent

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


async def run_agent(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
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
        },
        note=note,
        started_at=_now(),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    await bus.publish("agent.started", {"batch_id": batch.id, "agent": agent.value, "run_id": run.id})
    await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})

    try:
        output = await run_mock_agent(agent, product, batch)
    except Exception as exc:  # pragma: no cover - mock never fails, real agents will
        run.status = "failed"
        run.error = str(exc)
        run.finished_at = _now()
        batch.state = review_state
        await session.commit()
        await bus.publish(
            "agent.failed",
            {"batch_id": batch.id, "agent": agent.value, "run_id": run.id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail="Agent 运行失败") from exc

    run.status = "waiting_review"
    run.output_json = output
    run.finished_at = _now()
    setattr(batch, AGENT_FIELD[agent], output)
    batch.state = review_state
    await session.commit()
    await session.refresh(run)
    await session.refresh(batch)
    await bus.publish(
        "agent.completed",
        {"batch_id": batch.id, "agent": agent.value, "run_id": run.id, "status": run.status},
    )
    await bus.publish("batch.updated", {"batch_id": batch.id, "state": batch.state})
    return run


async def approve_agent(
    session: AsyncSession,
    batch: Batch,
    agent: AgentName,
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

    artifact = Artifact(
        batch_id=batch.id,
        agent_run_id=run.id,
        kind=agent.value,
        content_json=content,
        approved_at=_now(),
    )
    session.add(artifact)
    run.status = "approved"
    run.output_json = content
    setattr(batch, AGENT_FIELD[agent], content)
    batch.state = f"{agent.value}_approved"

    if agent == AgentName.PRICING:
        if not batch.trace_code:
            batch.trace_code = f"ZT{batch.id:04d}"
        batch.state = "traced"
        batch.current_station = "trace"

    await session.commit()
    await session.refresh(artifact)
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
