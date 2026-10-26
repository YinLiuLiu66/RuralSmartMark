from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentRun, Artifact, Batch

DEMO_BATCH_CODE = "ZT-DEMO-001"
ACTIVE_RUN_STATUSES = ("queued", "running")
# 进程崩溃可能遗留 running 状态的 run；超过该时长视为陈旧，放行删除
STALE_RUN_AFTER = timedelta(seconds=600)


class BatchDeleteError(RuntimeError):
    """批次不可删除；消息可直接展示给用户。"""


def _run_is_stale(run: AgentRun) -> bool:
    # AgentRun 没有更新时间，用 started_at 判断；没开始过的 run 保守视为活跃
    started = run.started_at
    if started is None:
        return False
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return datetime.now(UTC) - started > STALE_RUN_AFTER


async def _active_runs(session: AsyncSession, batch_id: int) -> list[AgentRun]:
    return list(
        (
            await session.execute(
                select(AgentRun).where(
                    AgentRun.batch_id == batch_id,
                    AgentRun.status.in_(ACTIVE_RUN_STATUSES),
                )
            )
        )
        .scalars()
        .all()
    )


async def ensure_deletable(session: AsyncSession, batch: Batch) -> None:
    """校验批次当前可删；不可删时抛 BatchDeleteError。"""
    if batch.code == DEMO_BATCH_CODE:
        raise BatchDeleteError(
            f"{DEMO_BATCH_CODE} 是固定演示批次，删除后演示动线会断，不允许删除。"
        )
    active = await _active_runs(session, batch.id)
    if any(not _run_is_stale(run) for run in active):
        raise BatchDeleteError("该批次还有正在运行的 Agent 任务，等它结束或失败后再删除。")


async def delete_batch(session: AsyncSession, batch: Batch) -> dict:
    """删除批次：先清产物文件，再借外键级联清运行/产物/扫码/对话记录。"""
    await ensure_deletable(session, batch)

    artifacts = list(
        (
            await session.execute(select(Artifact).where(Artifact.batch_id == batch.id))
        )
        .scalars()
        .all()
    )
    removed_files = 0
    for artifact in artifacts:
        if artifact.file_path:
            Path(artifact.file_path).unlink(missing_ok=True)
            removed_files += 1

    runs_count = await session.scalar(
        select(func.count()).select_from(AgentRun).where(AgentRun.batch_id == batch.id)
    )
    code = batch.code
    await session.delete(batch)
    await session.commit()
    return {
        "code": code,
        "runs": runs_count or 0,
        "artifacts": len(artifacts),
        "files": removed_files,
    }
