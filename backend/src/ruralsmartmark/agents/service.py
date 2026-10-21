"""Agent 任务执行（decisions #25/#26）：先落库、再广播，失败落 failed。

后台任务由路由用 FastAPI BackgroundTasks 调度；每次状态变更独立 session，
LLM 调用期间不持有事务。空 key 走 mock（#11 断网兜底 / 测试）。
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ruralsmartmark import db
from ruralsmartmark.agents import llm, mock
from ruralsmartmark.agents.context import collect_facts
from ruralsmartmark.agents.prompts import build_copy_messages, build_story_messages
from ruralsmartmark.models import AgentArtifact, AgentTask
from ruralsmartmark.sim.engine import engine
from ruralsmartmark.ws.bus import bus

logger = logging.getLogger(__name__)

KIND_BY_TYPE = {"story": "story", "copy": "copy"}
MATERIAL_PATH = Path(__file__).parent / "materials" / "majiang.json"


@lru_cache
def load_material() -> dict[str, Any]:
    return json.loads(MATERIAL_PATH.read_text(encoding="utf-8"))


def sim_time_iso() -> str:
    return engine.clock.sim_time.isoformat(timespec="seconds")


def task_to_dict(task: AgentTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "agent_type": task.agent_type,
        "status": task.status,
        "product_sku_id": task.product_sku_id,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "artifacts": [
            {
                "id": a.id,
                "kind": a.kind,
                "content": a.content,
                "asset_url": a.asset_url,
                "status": a.status,
                "updated_at": a.updated_at,
            }
            for a in task.artifacts
        ],
    }


async def load_task(task_id: int) -> AgentTask | None:
    async with db.session_factory() as session:
        return await session.scalar(
            select(AgentTask)
            .options(selectinload(AgentTask.artifacts))
            .where(AgentTask.id == task_id)
        )


async def broadcast_task(task_id: int) -> None:
    task = await load_task(task_id)
    if task is None:
        return
    await bus.broadcast("agent.task_updated", task_to_dict(task), sim_time_iso())


async def _latest_story(session: Any, sku_id: int | None) -> str | None:
    query = select(AgentArtifact).where(AgentArtifact.kind == "story")
    if sku_id is not None:
        query = query.join(AgentTask).where(AgentTask.product_sku_id == sku_id)
    artifact = await session.scalar(query.order_by(AgentArtifact.id.desc()).limit(1))
    return artifact.content if artifact is not None else None


async def run_task(task_id: int) -> None:
    async with db.session_factory() as session:
        task = await session.get(AgentTask, task_id)
        if task is None or task.status != "pending":
            return
        task.status = "running"
        await session.commit()
        agent_type = task.agent_type
        sku_id = task.product_sku_id

    await broadcast_task(task_id)

    try:
        async with db.session_factory() as session:
            facts = await collect_facts(session, sku_id)
            story = (
                await _latest_story(session, sku_id)
                if agent_type == "copy"
                else None
            )

        material = load_material()
        if agent_type == "story":
            messages = build_story_messages(material, facts)
        else:
            messages = build_copy_messages(material, facts, story)

        if llm.is_configured():
            content = await llm.complete(messages)
        else:
            content = mock.render(agent_type, material, facts)

        async with db.session_factory() as session:
            task = await session.get(AgentTask, task_id)
            if task is None:
                return
            task.status = "done"
            kind = KIND_BY_TYPE.get(agent_type, agent_type)
            artifact = await session.scalar(
                select(AgentArtifact).where(
                    AgentArtifact.task_id == task_id, AgentArtifact.kind == kind
                )
            )
            if artifact is None:
                artifact = AgentArtifact(
                    task_id=task_id, kind=kind, content=content, status="draft"
                )
                session.add(artifact)
            else:
                artifact.content = content
                artifact.status = "draft"
            await session.commit()
            artifact_id = artifact.id

        await broadcast_task(task_id)
        await bus.broadcast(
            "agent.artifact_ready",
            {"task_id": task_id, "artifact_id": artifact_id, "kind": kind},
            sim_time_iso(),
        )
    except Exception as e:  # noqa: BLE001 — 任务失败不反噬主循环，落 failed 后广播
        logger.exception("agent task %s failed: %s", task_id, e)
        async with db.session_factory() as session:
            task = await session.get(AgentTask, task_id)
            if task is not None:
                task.status = "failed"
                await session.commit()
        await broadcast_task(task_id)
