from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.base import AgentName
from ..agents.controller import ControllerUnavailable, run_controller_turn
from ..agents.orchestrator import (
    approve_agent,
    next_agent,
    reject_agent,
)
from ..agents.orchestrator import (
    run_agent as run_pipeline_agent,
)
from ..agents.runtime import RuntimeDep
from ..deps import SessionDep, SessionFactoryDep
from ..models import Batch, ControllerMessage, ControllerSession, ProductProfile
from ..providers.search import SearchProvider, get_search_provider
from ..schemas import (
    ControllerConfirmIn,
    ControllerMessageIn,
    ControllerMessageOut,
    ControllerPageContext,
    ControllerSessionCreate,
    ControllerSessionOut,
    ControllerTurnOut,
    ResearchDraft,
)
from ..services.batch_create import (
    DEFAULT_QUANTITY_KG,
    BatchCreateError,
    create_batch_for_product,
)
from ..services.batch_delete import BatchDeleteError, delete_batch
from ..services.controller_context import (
    PageContextError,
    PendingTargetError,
    draft_hash,
    history_content,
    pending_batch,
    pending_product,
    resolve_page_context,
)
from ..services.products import apply_user_inputs, commit_research_draft
from ..services.rewind import rewind_to_agent

router = APIRouter()


class ControllerBusy(RuntimeError):
    """同一时间只允许一轮总控操作（消息或确认）。"""


_locks: dict[int, asyncio.Lock] = {}


def _turn_lock() -> asyncio.Lock:
    """按事件循环懒建锁：测试每个用例一个新 loop，模块级锁会绑到旧 loop。"""
    loop = asyncio.get_running_loop()
    lock = _locks.get(id(loop))
    if lock is None:
        lock = asyncio.Lock()
        _locks[id(loop)] = lock
    return lock


def _acquire_turn_lock() -> asyncio.Lock:
    lock = _turn_lock()
    if lock.locked():
        # fail-fast：确认通过可能自动跑下一站，排队会让另一个标签页空转。
        raise ControllerBusy("总控正在处理上一条消息，请稍候再发")
    return lock


async def _messages(session: SessionDep, session_id: int) -> list[ControllerMessage]:
    rows = await session.execute(
        select(ControllerMessage)
        .where(ControllerMessage.session_id == session_id)
        .order_by(ControllerMessage.id)
    )
    return list(rows.scalars().all())


async def _session_out(session: SessionDep, item: ControllerSession) -> ControllerSessionOut:
    messages = await _messages(session, item.id)
    product = await session.get(ProductProfile, item.product_id) if item.product_id else None
    batch = await session.get(Batch, item.batch_id) if item.batch_id else None
    if product is not None:
        await session.refresh(product)
    if batch is not None:
        await session.refresh(batch)
    return ControllerSessionOut(
        id=item.id,
        product_id=item.product_id,
        batch_id=item.batch_id,
        product_name=product.name if product else None,
        batch_code=batch.code if batch else None,
        batch_state=batch.state if batch else None,
        draft_json=item.draft_json,
        pending_action_json=item.pending_action_json,
        messages=[ControllerMessageOut.model_validate(message) for message in messages],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _global_session(session: AsyncSession) -> ControllerSession:
    """总控全局只有一条会话（decisions #92）：有则复用，无则新建。"""
    item = await session.scalar(
        select(ControllerSession).order_by(ControllerSession.id.desc())
    )
    if item is not None:
        return item

    item = ControllerSession()
    session.add(item)
    try:
        await session.commit()
    except IntegrityError:
        # 并发下另一个请求已插入；回滚后复用同一行。
        await session.rollback()
        existing = await session.scalar(
            select(ControllerSession).order_by(ControllerSession.id.desc())
        )
        if existing is None:
            raise
        return existing
    await session.refresh(item)
    return item


@router.post("/controller/sessions", response_model=ControllerSessionOut)
async def create_controller_session(
    session: SessionDep,
    payload: ControllerSessionCreate | None = None,
) -> ControllerSessionOut:
    # product_slug / batch_id / fresh 已废弃（decisions #92）：总控只有一条全局会话，
    # 当前页面由每条消息携带的 page_context 决定，不再靠会话绑定。
    del payload
    return await _session_out(session, await _global_session(session))


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
    page_context: ControllerPageContext | None = None,
    emit: Callable[[dict], Awaitable[None]] | None = None,
) -> ControllerTurnOut:
    async with _acquire_turn_lock():
        return await _run_turn_locked(
            session, item, message, runtime, page_context=page_context, emit=emit
        )


async def _run_turn_locked(
    session: SessionDep,
    item: ControllerSession,
    message: str,
    runtime: RuntimeDep,
    *,
    page_context: ControllerPageContext | None = None,
    emit: Callable[[dict], Awaitable[None]] | None = None,
) -> ControllerTurnOut:
    page = await resolve_page_context(session, page_context)
    # 页面目标变了，旧确认卡不再可信（decisions #92）。
    if (
        item.pending_action_json
        and page.batch is not None
        and item.pending_action_json.get("batch_id") != page.batch.id
    ):
        item.pending_action_json = None
        await session.commit()
    history = [
        (row.id, row.role, history_content(row.action_json, row.content))
        for row in await _messages(session, item.id)
    ]
    page_label = page.label
    user_message = ControllerMessage(
        session_id=item.id,
        role="user",
        content=message,
        action_json=(
            {"page_context": page.as_dict(), "page_label": page_label}
            if page_label
            else None
        ),
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
            page=page,
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
        needs_target=turn.needs_target,
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
    try:
        return await _run_turn(
            session, item, payload.message, runtime, page_context=payload.context
        )
    except PageContextError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ControllerBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
                    db_session,
                    item,
                    payload.message,
                    runtime,
                    page_context=payload.context,
                    emit=emit,
                )
                await queue.put({"type": "done", "turn": turn.model_dump(mode="json")})
        except PageContextError as exc:
            await queue.put({"type": "error", "detail": str(exc)})
        except ControllerBusy as exc:
            await queue.put({"type": "error", "detail": str(exc)})
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
    try:
        async with _acquire_turn_lock():
            pending = item.pending_action_json or {}
            if pending.get("id") != payload.action_id:
                raise HTTPException(status_code=409, detail="确认动作已失效，请重新发起")

            if payload.decision == "cancel":
                item.pending_action_json = None
                content = "已取消，没有改动数据。"
            else:
                # 先置空再执行：两个标签页重复点击时，第二次必然失效。
                item.pending_action_json = None
                await session.commit()
                content = await _execute_pending(session, item, pending, runtime)

            assistant = ControllerMessage(
                session_id=item.id,
                role="assistant",
                content=content,
                action_json={
                    "confirmed": pending.get("kind"),
                    "decision": payload.decision,
                },
            )
            session.add(assistant)
            await session.commit()
            await session.refresh(item)
            return ControllerTurnOut(
                session=await _session_out(session, item),
                reply=content,
                pending_action=None,
            )
    except ControllerBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def _execute_pending(
    session: SessionDep,
    item: ControllerSession,
    pending: dict,
    runtime: RuntimeDep,
) -> str:
    try:
        return await _execute_pending_locked(session, item, pending, runtime)
    except PendingTargetError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _verify_draft(pending: dict, draft_json: dict | None) -> None:
    frozen = pending.get("draft_sha256")
    if frozen and frozen != draft_hash(draft_json):
        raise PendingTargetError("草案已被新的调研或录入覆盖，请重新发起确认")


async def _execute_pending_locked(
    session: SessionDep,
    item: ControllerSession,
    pending: dict,
    runtime: RuntimeDep,
) -> str:
    kind = pending.get("kind")
    if kind == "commit_product":
        if not item.draft_json:
            raise HTTPException(status_code=409, detail="没有可提交的产品草案")
        _verify_draft(pending, item.draft_json)
        draft = ResearchDraft.model_validate(item.draft_json)
        product, new_batch, docs, benchmarks = await commit_research_draft(session, draft)
        product_name, product_slug, batch_code = (
            product.name,
            product.slug,
            new_batch.code,
        )
        item.product_id = product.id
        item.batch_id = new_batch.id
        item.draft_json = None
        item.pending_action_json = None
        await session.commit()
        return (
            f"已建档：{product_name}（{product_slug}），"
            f"知识库 {docs} 条、基准价 {benchmarks} 条，批次 {batch_code}。"
        )

    if kind == "apply_inputs":
        if not item.draft_json:
            raise HTTPException(status_code=409, detail="没有可写入的数据草案")
        _verify_draft(pending, item.draft_json)
        product = await pending_product(session, pending)
        draft = ResearchDraft.model_validate(item.draft_json)
        if draft.product.slug != product.slug:
            raise PendingTargetError(
                f"草案属于 {draft.product.slug}，与确认卡目标 {product.slug} 不一致，请重新发起"
            )
        stats = await apply_user_inputs(session, product, draft)
        item.pending_action_json = None
        item.draft_json = None
        await session.commit()
        costs = stats["cost_assumptions"]
        return (
            f"已写入 {product.name} 的档案：成本口径 {len(costs)} 项、"
            f"基准价 {stats['benchmarks']} 条、事实 {stats['docs']} 条。"
            "档案已更新，但已有产出不会自动重算——要重新跑到定价站才生效。"
        )

    if kind == "create_batch":
        product = await pending_product(session, pending)
        raw_quantity = pending.get("quantity_kg")
        try:
            quantity = float(raw_quantity) if raw_quantity else 0.0
        except (TypeError, ValueError):
            quantity = 0.0
        try:
            batch = await create_batch_for_product(
                session, product, quantity if quantity > 0 else DEFAULT_QUANTITY_KG
            )
        except BatchCreateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        item.batch_id = batch.id
        item.pending_action_json = None
        await session.commit()
        return (
            f"已为 {product.name} 创建新批次 {batch.code}（{batch.quantity_kg:g} kg），"
            "会话已切换到该批次，可直接运行流水线。"
        )

    if kind == "delete_batch":
        batch = await pending_batch(session, pending)
        try:
            stats = await delete_batch(session, batch)
        except BatchDeleteError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        item.batch_id = None
        item.pending_action_json = None
        await session.commit()
        return (
            f"已删除批次 {stats['code']}：清理 {stats['runs']} 条运行记录、"
            f"{stats['artifacts']} 个产物（删除 {stats['files']} 个文件）。"
            "会话已不再绑定批次，可切换批次或新建。"
        )

    batch = await pending_batch(session, pending)
    agent_value = pending.get("agent") or ""
    try:
        agent = AgentName(agent_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"未知 Agent: {agent_value}") from exc

    if kind == "approve_agent":
        await approve_agent(session, batch, agent, runtime)
        result = f"已通过 {agent.value}。"
        upcoming = next_agent(batch)
        if upcoming is None:
            if batch.state == "traced":
                result += f" 批次已进入溯源状态，溯源码 {batch.trace_code}。"
        else:
            try:
                next_run = await run_pipeline_agent(session, batch, upcoming, runtime)
            except Exception as exc:  # noqa: BLE001 - 审核已完成，下一站失败不回滚
                result += (
                    f" 下一站 {upcoming.value} 启动失败：{str(exc)[:200]}。"
                    "可到对应工位重跑。"
                )
            else:
                if next_run.status == "waiting_review":
                    result += f" 已自动运行 {upcoming.value}，产出待审核。"
                elif next_run.status == "approved":
                    result += f" 已自动运行并通过 {upcoming.value}。"
                else:
                    result += f" 已自动运行 {upcoming.value}，当前状态 {next_run.status}。"
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
