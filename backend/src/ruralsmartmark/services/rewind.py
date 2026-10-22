from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.base import AgentName
from ..agents.runtime import AgentRuntime
from ..models import AgentRun, Artifact, Batch

AGENT_ORDER = [
    AgentName.STORY,
    AgentName.PACKAGING,
    AgentName.MARKETING,
    AgentName.PRICING,
]
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
STAGE_INDEX = {
    "raw": 0,
    "story_running": 0,
    "story_review": 0,
    "story_approved": 1,
    "packaging_running": 1,
    "packaging_review": 1,
    "packaging_approved": 2,
    "marketing_running": 2,
    "marketing_review": 2,
    "marketing_approved": 3,
    "pricing_running": 3,
    "pricing_review": 3,
    "traced": 4,
}


def _downstream(target: AgentName) -> list[AgentName]:
    start = AGENT_ORDER.index(target)
    return AGENT_ORDER[start:]


async def rewind_to_agent(
    session: AsyncSession,
    batch: Batch,
    target: AgentName,
    runtime: AgentRuntime,
    note: str | None = None,
) -> AgentRun:
    if batch.state == f"{target.value}_review":
        from ..agents.orchestrator import run_agent

        return await run_agent(session, batch, target, runtime, note)

    target_index = AGENT_ORDER.index(target)
    current_index = STAGE_INDEX.get(batch.state, -1)
    if current_index < target_index:
        raise ValueError(f"批次当前状态 {batch.state} 还不能跑到 {target.value}")

    names = [agent.value for agent in _downstream(target)]
    for agent in _downstream(target):
        setattr(batch, AGENT_FIELD[agent], None)
    batch.trace_code = None
    batch.state = READY_STATE[target]
    batch.current_station = target.value

    runs = list(
        (
            await session.execute(
                select(AgentRun).where(
                    AgentRun.batch_id == batch.id,
                    AgentRun.agent.in_(names),
                )
            )
        )
        .scalars()
        .all()
    )
    for run in runs:
        if run.status in {"approved", "waiting_review", "running"}:
            run.status = "failed"
            run.error = "rewound by controller"

    artifact_kinds = set(names)
    if target_index <= AGENT_ORDER.index(AgentName.PACKAGING):
        artifact_kinds.add("illustration")
    artifacts = list(
        (
            await session.execute(
                select(Artifact).where(
                    Artifact.batch_id == batch.id,
                    Artifact.kind.in_(artifact_kinds),
                )
            )
        )
        .scalars()
        .all()
    )
    for artifact in artifacts:
        if artifact.file_path:
            Path(artifact.file_path).unlink(missing_ok=True)
        await session.delete(artifact)
    await session.commit()

    from ..agents.orchestrator import run_agent

    return await run_agent(session, batch, target, runtime, note)
