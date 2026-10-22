import json

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from ..agents.base import AgentName
from ..agents.orchestrator import approve_agent, next_agent, reject_agent, run_agent
from ..agents.runtime import RuntimeDep
from ..deps import SessionDep
from ..models import AgentRun, Batch, ProductProfile
from ..schemas import (
    AgentRunRequest,
    ApproveRequest,
    BatchWorkspaceOut,
    PackagingVariantOut,
    RejectRequest,
)
from ..services.events import bus
from ..services.packaging import (
    PACKAGING_VARIANTS,
    list_packaging_variants,
    render_label_png_bytes,
)
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
async def start_pipeline(
    batch_id: int, session: SessionDep, runtime: RuntimeDep
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    if batch.state == "traced":
        return await _workspace_or_404(session, batch_id)
    if batch.state.endswith("_review"):
        raise HTTPException(status_code=409, detail="当前步骤待审核")

    agent = next_agent(batch)
    if agent is None:
        raise HTTPException(status_code=409, detail="当前批次没有可运行步骤")

    await run_agent(session, batch, agent, runtime)
    return await _workspace_or_404(session, batch_id)


@router.post("/batches/{batch_id}/agents/{agent}/run", response_model=BatchWorkspaceOut)
async def run_specific_agent(
    batch_id: int,
    agent: str,
    payload: AgentRunRequest,
    session: SessionDep,
    runtime: RuntimeDep,
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    await run_agent(session, batch, _agent_or_422(agent), runtime, payload.note)
    return await _workspace_or_404(session, batch_id)


@router.post("/batches/{batch_id}/agents/{agent}/approve", response_model=BatchWorkspaceOut)
async def approve_specific_agent(
    batch_id: int,
    agent: str,
    payload: ApproveRequest,
    session: SessionDep,
    runtime: RuntimeDep,
) -> BatchWorkspaceOut:
    batch = await _batch_or_404(session, batch_id)
    await approve_agent(session, batch, _agent_or_422(agent), runtime, payload.output)
    return await _workspace_or_404(session, batch_id)


@router.get(
    "/batches/{batch_id}/agents/packaging/variants",
    response_model=list[PackagingVariantOut],
)
async def packaging_variants(batch_id: int, session: SessionDep) -> list[dict]:
    await _batch_or_404(session, batch_id)
    return list_packaging_variants()


@router.get("/batches/{batch_id}/agents/packaging/preview")
async def packaging_preview(
    batch_id: int,
    session: SessionDep,
    runtime: RuntimeDep,
    variant: str = "kraft",
) -> Response:
    batch = await _batch_or_404(session, batch_id)
    if variant not in PACKAGING_VARIANTS:
        raise HTTPException(status_code=422, detail="未知包装变体")
    run = await session.scalar(
        select(AgentRun)
        .where(
            AgentRun.batch_id == batch_id,
            AgentRun.agent == AgentName.PACKAGING.value,
            AgentRun.output_json.is_not(None),
        )
        .order_by(AgentRun.id.desc())
    )
    if run is None or not run.output_json:
        raise HTTPException(status_code=404, detail="还没有包装产出")
    product = await session.get(ProductProfile, batch.product_id)
    if product is None:
        raise HTTPException(status_code=409, detail="产品档案缺失")
    png = render_label_png_bytes(
        run.output_json,
        batch,
        product,
        public_base_url=runtime.settings.public_base_url,
        variant=variant,
    )
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


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
