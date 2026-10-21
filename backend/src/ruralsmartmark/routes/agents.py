"""Agent 任务路由（03 §3.2，decisions #25/#26）。

鉴权：两个角色都能发起；operator 可编辑/润色/定稿，coop 只能改自己草稿。
执行：BackgroundTasks 调度，产出物先落库、后广播（沿 M2 铁律）。
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ruralsmartmark.agents.service import broadcast_task, run_task
from ruralsmartmark.auth import ROLE_COOP, ROLE_OPERATOR, User, get_current_user
from ruralsmartmark.db import get_session
from ruralsmartmark.models import AgentArtifact, AgentTask, ProductSku
from ruralsmartmark.schemas.agents import (
    AgentArtifactOut,
    AgentArtifactUpdate,
    AgentTaskCreate,
    AgentTaskOut,
)

router = APIRouter(prefix="/api", tags=["agents"])

ALLOWED_TRANSITIONS = {
    "draft": {"polished", "final"},
    "polished": {"final"},
}


def _ensure_role(user: User) -> None:
    if user.role not in (ROLE_OPERATOR, ROLE_COOP):
        raise HTTPException(status_code=403, detail="无权限执行该操作")


async def _load_task(session: AsyncSession, task_id: int) -> AgentTask:
    task = await session.scalar(
        select(AgentTask)
        .options(selectinload(AgentTask.artifacts))
        .where(AgentTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post(
    "/agent-tasks", response_model=AgentTaskOut, status_code=status.HTTP_201_CREATED
)
async def create_agent_task(
    payload: AgentTaskCreate,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentTaskOut:
    _ensure_role(user)
    if payload.product_sku_id is not None:
        sku = await session.get(ProductSku, payload.product_sku_id)
        if sku is None:
            raise HTTPException(status_code=404, detail="产品不存在")

    task = AgentTask(
        agent_type=payload.agent_type,
        product_sku_id=payload.product_sku_id,
        created_by=user.username,
        status="pending",
    )
    session.add(task)
    await session.commit()

    loaded = await _load_task(session, task.id)
    background_tasks.add_task(run_task, task.id)
    return AgentTaskOut.model_validate(loaded)


@router.get("/agent-tasks", response_model=list[AgentTaskOut])
async def list_agent_tasks(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AgentTaskOut]:
    _ensure_role(user)
    tasks = (
        await session.scalars(
            select(AgentTask)
            .options(selectinload(AgentTask.artifacts))
            .order_by(AgentTask.id.desc())
            .limit(50)
        )
    ).all()
    return [AgentTaskOut.model_validate(t) for t in tasks]


@router.get("/agent-tasks/{task_id}", response_model=AgentTaskOut)
async def get_agent_task(
    task_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentTaskOut:
    _ensure_role(user)
    return AgentTaskOut.model_validate(await _load_task(session, task_id))


@router.patch("/agent-artifacts/{artifact_id}", response_model=AgentArtifactOut)
async def update_agent_artifact(
    artifact_id: int,
    payload: AgentArtifactUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentArtifactOut:
    _ensure_role(user)
    artifact = await session.get(AgentArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="产出物不存在")
    task = await session.get(AgentTask, artifact.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if user.role != ROLE_OPERATOR:
        if task.created_by != user.username:
            raise HTTPException(status_code=403, detail="只能编辑自己的产出物")
        if payload.status is not None:
            raise HTTPException(status_code=403, detail="合作社只能编辑草稿内容")
        if artifact.status != "draft":
            raise HTTPException(status_code=403, detail="只能编辑草稿")

    if artifact.status == "final":
        raise HTTPException(status_code=409, detail="定稿后不可修改")

    if payload.status is not None:
        allowed = ALLOWED_TRANSITIONS.get(artifact.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"不允许从 {artifact.status} 流转到 {payload.status}",
            )
        artifact.status = payload.status

    if payload.content is not None:
        artifact.content = payload.content

    await session.commit()
    await session.refresh(artifact)
    await broadcast_task(task.id)
    return AgentArtifactOut.model_validate(artifact)


@router.get("/agent-artifacts/{artifact_id}", response_model=AgentArtifactOut)
async def get_agent_artifact(
    artifact_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AgentArtifactOut:
    _ensure_role(user)
    artifact = await session.get(AgentArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="产出物不存在")
    return AgentArtifactOut.model_validate(artifact)
