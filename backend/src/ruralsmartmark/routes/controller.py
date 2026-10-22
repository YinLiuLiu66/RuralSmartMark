from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..agents.base import AgentName
from ..agents.controller import ControllerUnavailable, run_controller_turn
from ..agents.orchestrator import approve_agent, reject_agent
from ..agents.runtime import RuntimeDep
from ..deps import SessionDep, SessionFactoryDep
from ..models import Batch, ControllerMessage, ControllerSession, ProductProfile
from ..providers.search import SearchProvider, get_search_provider
from ..schemas import (
    ControllerConfirmIn,
    ControllerMessageIn,
    ControllerMessageOut,
    ControllerSessionCreate,
    ControllerSessionOut,
    ControllerTurnOut,
    ResearchDraft,
)
from ..services.products import commit_research_draft
from ..services.rewind import rewind_to_agent

router = APIRouter()


async def _messages(session: SessionDep, session_id: int) -> list[ControllerMessage]:
    rows = await session.execute(
        select(ControllerMessage)
        .where(ControllerMessage.session_id == session_id)
        .order_by(ControllerMessage.id)
    )
    return list(rows.scalars().all())


async def _session_out(session: SessionDep, item: ControllerSession) -> ControllerSessionOut:
    messages = await _messages(session, item.id)
    return ControllerSessionOut(
        id=item.id,
        product_id=item.product_id,
        batch_id=item.batch_id,
        draft_json=item.draft_json,
        pending_action_json=item.pending_action_json,
        messages=[ControllerMessageOut.model_validate(message) for message in messages],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/controller/sessions", response_model=ControllerSessionOut)
async def create_controller_session(
    payload: ControllerSessionCreate, session: SessionDep
) -> ControllerSessionOut:
    product_id = None
    if payload.product_slug:
        product = await session.scalar(
            select(ProductProfile).where(ProductProfile.slug == payload.product_slug)
        )
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        product_id = product.id

    existing = await session.scalar(
        select(ControllerSession)
        .where(
            ControllerSession.product_id == product_id,
            ControllerSession.batch_id == payload.batch_id,
        )
        .order_by(ControllerSession.id.desc())
    )
    if existing is not None:
        return await _session_out(session, existing)

    item = ControllerSession(product_id=product_id, batch_id=payload.batch_id)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return await _session_out(session, item)


@router.get("/controller/sessions/{session_id}", response_model=ControllerSessionOut)
async def get_controller_session(session_id: int, session: SessionDep) -> ControllerSessionOut:
    item = await session.get(ControllerSession, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="controller session not found")
    return await _session_out(session, item)


async def _run_turn(
    session: SessionDep,
    item: ControllerSession,
    message: str,
    runtime: RuntimeDep,
    *,
    emit: Callable[[dict], Awaitable[None]] | None = None,
) -> ControllerTurnOut:
    history = [
        (row.role, row.content) for row in await _messages(session, item.id)
    ]
    user_message = ControllerMessage(
        session_id=item.id,
        role="user",
        content=message,
    )
    session.add(user_message)
    await session.commit()
    await session.refresh(user_message)
    if emit is not None:
        await emit(
            {
                "type": "user",
                "message": ControllerMessageOut.model_validate(user_message).model_dump(
                    mode="json"
                ),
            }
        )

    search: SearchProvider = get_search_provider(runtime.settings)
    try:
        turn = await run_controller_turn(
            session,
            runtime,
            item,
            message,
            search=search,
            history=history,
            emit=emit,
        )
    except ControllerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    assistant = ControllerMessage(
        session_id=item.id,
        role="assistant",
        content=turn.reply,
        action_json={
            "questions": turn.questions,
            "pending_action": turn.pending,
            "events": turn.events,
            "thinking": turn.thinking,
        },
    )
    session.add(assistant)
    if turn.draft is not None:
        item.draft_json = turn.draft.model_dump(mode="json")
    if turn.pending is not None:
        item.pending_action_json = turn.pending
    await session.commit()
    await session.refresh(item)
    return ControllerTurnOut(
        session=await _session_out(session, item),
        reply=turn.reply,
        questions=turn.questions,
        pending_action=turn.pending,
        events=turn.events,
        thinking=turn.thinking,
    )


@router.post("/controller/sessions/{session_id}/messages", response_model=ControllerTurnOut)
async def post_controller_message(
    session_id: int,
    payload: ControllerMessageIn,
    session: SessionDep,
    runtime: RuntimeDep,
) -> ControllerTurnOut:
    item = await session.get(ControllerSession, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="controller session not found")
    return await _run_turn(session, item, payload.message, runtime)


@router.post("/controller/sessions/{session_id}/messages/stream")
async def stream_controller_message(
    session_id: int,
    payload: ControllerMessageIn,
    runtime: RuntimeDep,
    session_factory: SessionFactoryDep,
) -> StreamingResponse:
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def worker() -> None:
        try:
            async with session_factory() as db_session:
                item = await db_session.get(ControllerSession, session_id)
                if item is None:
                    await queue.put({"type": "error", "detail": "总控会话不存在"})
                    return
                turn = await _run_turn(
                    db_session, item, payload.message, runtime, emit=emit
                )
                await queue.put({"type": "done", "turn": turn.model_dump(mode="json")})
        except ControllerUnavailable as exc:
            await queue.put({"type": "error", "detail": str(exc)})
        except HTTPException as exc:
            await queue.put({"type": "error", "detail": str(exc.detail)})
        except Exception as exc:  # noqa: BLE001 - SSE 必须把失败转成可见事件
            await queue.put({"type": "error", "detail": f"总控调用失败：{str(exc)[:240]}"})
        finally:
            await queue.put(None)

    task = asyncio.create_task(worker())

    async def stream():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/controller/sessions/{session_id}/confirm", response_model=ControllerTurnOut)
async def confirm_controller_action(
    session_id: int,
    payload: ControllerConfirmIn,
    session: SessionDep,
    runtime: RuntimeDep,
) -> ControllerTurnOut:
    item = await session.get(ControllerSession, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="controller session not found")
    pending = item.pending_action_json or {}
    if pending.get("id") != payload.action_id:
        raise HTTPException(status_code=409, detail="确认动作已失效，请重新发起")

    if payload.decision == "cancel":
        item.pending_action_json = None
        content = "已取消，没有改动数据。"
    else:
        content = await _execute_pending(session, item, pending, runtime)

    assistant = ControllerMessage(
        session_id=item.id,
        role="assistant",
        content=content,
        action_json={"confirmed": pending.get("kind"), "decision": payload.decision},
    )
    session.add(assistant)
    await session.commit()
    await session.refresh(item)
    return ControllerTurnOut(
        session=await _session_out(session, item),
        reply=content,
        pending_action=None,
    )


async def _execute_pending(
    session: SessionDep,
    item: ControllerSession,
    pending: dict,
    runtime: RuntimeDep,
) -> str:
    kind = pending.get("kind")
    if kind == "commit_product":
        if not item.draft_json:
            raise HTTPException(status_code=409, detail="没有可提交的产品草案")
        draft = ResearchDraft.model_validate(item.draft_json)
        product, new_batch, docs, benchmarks = await commit_research_draft(session, draft)
        item.product_id = product.id
        item.batch_id = new_batch.id
        item.draft_json = None
        item.pending_action_json = None
        await session.commit()
        return (
            f"已建档：{product.name}（{product.slug}），"
            f"知识库 {docs} 条、基准价 {benchmarks} 条，批次 {new_batch.code}。"
        )

    batch = await session.get(Batch, item.batch_id) if item.batch_id else None
    if batch is None:
        raise HTTPException(status_code=409, detail="当前没有批次")
    agent_value = pending.get("agent") or ""
    try:
        agent = AgentName(agent_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"未知 Agent: {agent_value}") from exc

    if kind == "approve_agent":
        await approve_agent(session, batch, agent, runtime)
        result = f"已通过 {agent.value}。"
    elif kind == "reject_agent":
        await reject_agent(session, batch, agent, pending.get("note") or None)
        result = f"已驳回 {agent.value}。"
    elif kind == "rewind_to_agent":
        await rewind_to_agent(session, batch, agent, runtime, pending.get("note") or None)
        result = f"已回退到 {agent.value} 并重跑，后续产出已作废。"
    else:
        raise HTTPException(status_code=422, detail=f"未知动作: {kind}")

    item.pending_action_json = None
    await session.commit()
    return result
