"""预生成演示内容并落库（decisions #11）：断网答辩也能命中真实产出。

运行：cd backend && uv run python -m ruralsmartmark.agents.pregenerate
幂等：已存在对应 kind 的 final 产出物则跳过；无 key 时走 mock（仍可离线演示）。
"""

import asyncio

from sqlalchemy import select

from ruralsmartmark import db
from ruralsmartmark.agents.service import run_task
from ruralsmartmark.models import AgentArtifact, AgentTask

KINDS = {"story": "story", "copy": "copy"}


async def _has_final(kind: str) -> bool:
    async with db.session_factory() as session:
        found = await session.scalar(
            select(AgentArtifact.id)
            .where(AgentArtifact.kind == kind, AgentArtifact.status == "final")
            .limit(1)
        )
        return found is not None


async def _create(agent_type: str) -> int:
    async with db.session_factory() as session:
        task = AgentTask(agent_type=agent_type, created_by="operator", status="pending")
        session.add(task)
        await session.commit()
        return task.id


async def _finalize(task_id: int) -> tuple[int, int]:
    async with db.session_factory() as session:
        task = await session.get(AgentTask, task_id)
        if task is None or task.status != "done":
            raise RuntimeError(f"任务 {task_id} 未完成，跳过定稿")
        artifact = await session.scalar(
            select(AgentArtifact).where(AgentArtifact.task_id == task_id)
        )
        if artifact is None:
            raise RuntimeError(f"任务 {task_id} 没有产出物")
        artifact.status = "final"
        await session.commit()
        return artifact.id, len(artifact.content or "")


async def main() -> None:
    for agent_type, kind in KINDS.items():
        if await _has_final(kind):
            print(f"skip: {kind} 已有定稿产出物")
            continue
        task_id = await _create(agent_type)
        print(f"run: {agent_type} task #{task_id} ...")
        await run_task(task_id)
        artifact_id, size = await _finalize(task_id)
        print(f"done: {kind} artifact #{artifact_id}，{size} 字，已定稿")


if __name__ == "__main__":
    asyncio.run(main())
