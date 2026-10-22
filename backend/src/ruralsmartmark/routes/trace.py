from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.runtime import RuntimeDep
from ..deps import SessionDep
from ..models import Batch, ChatMessage, ProductProfile, ScanEvent
from ..schemas import TraceChatOut, TraceChatRequest, TraceOut, TraceScanOut
from ..services.events import bus
from ..services.packaging import render_label_png_bytes, render_qr_png
from ..services.trace import load_trace
from ..services.trace_chat import answer_trace_question

router = APIRouter()


async def _scan_count(session: AsyncSession, batch_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count()).select_from(ScanEvent).where(ScanEvent.batch_id == batch_id)
        )
        or 0
    )


async def _traced_batch(session: AsyncSession, code: str) -> Batch:
    batch = await session.scalar(
        select(Batch).where(
            func.upper(Batch.trace_code) == code.strip().upper(),
            Batch.state == "traced",
        )
    )
    if batch is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    return batch


@router.get("/trace/{code}", response_model=TraceOut)
async def get_trace(code: str, session: SessionDep) -> TraceOut:
    trace = await load_trace(session, code)
    if trace is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    return trace


@router.get("/trace/{code}/packaging.png")
async def trace_packaging(code: str, session: SessionDep, runtime: RuntimeDep) -> Response:
    batch = await _traced_batch(session, code)
    if not batch.packaging_json:
        raise HTTPException(status_code=404, detail="包装产出不存在")
    product = await session.get(ProductProfile, batch.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="产品档案不存在")
    png = render_label_png_bytes(
        batch.packaging_json,
        batch,
        product,
        public_base_url=runtime.settings.public_base_url,
    )
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=60"},
    )


@router.get("/trace/{code}/qr.png")
async def trace_qr(code: str, session: SessionDep, runtime: RuntimeDep) -> Response:
    batch = await _traced_batch(session, code)
    trace_code = batch.trace_code
    if trace_code is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    url = f"{runtime.settings.public_base_url.rstrip('/')}/trace/{trace_code}"
    return Response(
        content=render_qr_png(url, box_size=10),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/trace/{code}/scan", response_model=TraceScanOut)
async def get_scan_count(code: str, session: SessionDep) -> TraceScanOut:
    batch = await _traced_batch(session, code)
    return TraceScanOut(scan_count=await _scan_count(session, batch.id), recorded=False)


@router.post("/trace/{code}/scan", response_model=TraceScanOut)
async def record_scan(code: str, request: Request, session: SessionDep) -> TraceScanOut:
    batch = await _traced_batch(session, code)
    trace_code = batch.trace_code
    if trace_code is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    session.add(
        ScanEvent(
            batch_id=batch.id,
            trace_code=trace_code,
            channel="qr",
            user_agent=(request.headers.get("user-agent") or "")[:500] or None,
        )
    )
    await session.commit()
    count = await _scan_count(session, batch.id)
    await bus.publish(
        "trace.scanned",
        {"batch_id": batch.id, "trace_code": trace_code, "scan_count": count},
    )
    return TraceScanOut(scan_count=count)


@router.post("/trace/{code}/chat", response_model=TraceChatOut)
async def chat_with_trace(
    code: str,
    payload: TraceChatRequest,
    session: SessionDep,
    runtime: RuntimeDep,
) -> TraceChatOut:
    batch = await _traced_batch(session, code)
    trace = await load_trace(session, code)
    if trace is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    result = await answer_trace_question(runtime, trace, payload.message)
    session.add(ChatMessage(batch_id=batch.id, role="user", content=payload.message.strip()))
    session.add(ChatMessage(batch_id=batch.id, role="assistant", content=result.reply))
    await session.commit()
    return result
