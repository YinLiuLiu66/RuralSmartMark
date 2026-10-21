import json

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from ..agents.base import AgentName
from ..agents.orchestrator import approve_agent, next_agent, reject_agent, run_agent
from ..deps import SessionDep
from ..models import Batch
from ..schemas import (
    AgentRunRequest,
    ApproveRequest,
    BatchWorkspaceOut,
    RejectRequest,
)
from ..services.events import bus
from ..services.workspace import load_workspace

router = APIRouter()


async def _batch_or_404(session: AsyncSession, batch_id: int) -> Batch:
    batch = await session.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return batch


async def _workspace_or_404(session: AsyncSession, batch_id: int) -> BatchWorkspaceOut:
    workspace = await load_workspace(session, batch_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return workspace


def _agent_or_422(agent: str) -> AgentName:
    try:
        return AgentName(agent)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="未知 Agent") from exc


@router.post("/batches/{batch_id}/pipeline/start", response_model=BatchWorkspaceOut)
async def start_pipeline(batch_id: int, session: SessionDep) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    if batch.state == "traced":
        return await _workspace_or_404(session, batch_id)
    if batch.state.endswith("_review"):
        raise HTTPException(status_code=409, detail="当前步骤待审核")

    agent = next_agent(batch)
    if agent is None:
        raise HTTPException(status_code=409, detail="当前批次没有可运行步骤")

    await run_agent(session, batch, agent)
    return await _workspace_or_404(session, batch_id)


@router.post("/batches/{batch_id}/agents/{agent}/run", response_model=BatchWorkspaceOut)
async def run_specific_agent(
    batch_id: int,
    agent: str,
    payload: AgentRunRequest,
    session: SessionDep,
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    await run_agent(session, batch, _agent_or_422(agent), payload.note)
    return await _workspace_or_404(session, batch_id)


@router.post("/batches/{batch_id}/agents/{agent}/approve", response_model=BatchWorkspaceOut)
async def approve_specific_agent(
    batch_id: int,
    agent: str,
    payload: ApproveRequest,
    session: SessionDep,
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    await approve_agent(session, batch, _agent_or_422(agent), payload.output)
    return await _workspace_or_404(session, batch_id)


@router.post("/batches/{batch_id}/agents/{agent}/reject", response_model=BatchWorkspaceOut)
async def reject_specific_agent(
    batch_id: int,
    agent: str,
    payload: RejectRequest,
    session: SessionDep,
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    await reject_agent(session, batch, _agent_or_422(agent), payload.note)
    return await _workspace_or_404(session, batch_id)


@router.get("/batches/{batch_id}/events")
async def batch_events(batch_id: int, session: SessionDep):
    batch = await _batch_or_404(session, batch_id)

    async def event_generator():
        yield {
            "event": "message",
            "data": json.dumps({"type": "connected", "batch_id": batch.id}, ensure_ascii=False),
        }
        async for event in bus.subscribe():
            if event["data"].get("batch_id") != batch_id:
                continue
            payload = {"type": event["type"], **event["data"]}
            yield {
                "event": "message",
                "id": str(event["id"]),
                "data": json.dumps(payload, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator(), ping=15)
