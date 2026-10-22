from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from pydantic_ai import Agent, AgentRunResultEvent, RunContext
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
)
from pydantic_ai.usage import UsageLimits
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models import Batch, ControllerSession, ProductProfile
from ..providers.search import SearchProvider
from ..schemas import ResearchDraft
from ..services.rewind import AGENT_ORDER, STAGE_INDEX
from ..services.workspace import load_workspace
from .base import AgentName
from .pydantic_model import build_model_settings, build_pydantic_model
from .research import ResearchUnavailable, run_research
from .runtime import AgentRuntime


class ControllerUnavailable(RuntimeError):
    """总控无法调用模型；前端显示可操作提示。"""


@dataclass(slots=True)
class ControllerDeps:
    session: AsyncSession
    runtime: AgentRuntime
    settings: Settings
    search: SearchProvider
    product: ProductProfile | None = None
    batch: Batch | None = None
    draft: ResearchDraft | None = None
    pending: dict | None = None
    events: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class ControllerTurn:
    reply: str
    draft: ResearchDraft | None
    pending: dict | None
    events: list[dict]
    questions: list[str] = field(default_factory=list)
    thinking: list[str] = field(default_factory=list)


def _thinking_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:200]


def _summary_output(output: dict | None) -> str:
    if not output:
        return "（无产出）"
    text = json.dumps(output, ensure_ascii=False)
    return text[:600] + ("…" if len(text) > 600 else "")


def _workspace_summary(workspace) -> dict:
    return {
        "batch": {
            "id": workspace.batch.id,
            "code": workspace.batch.code,
            "state": workspace.batch.state,
            "trace_code": workspace.batch.trace_code,
            "quantity_kg": workspace.batch.quantity_kg,
        },
        "runs": [
            {
                "agent": run.agent,
                "status": run.status,
                "note": run.note,
                "error": run.error,
                "model": run.model,
                "output_preview": _summary_output(run.output_json),
            }
            for run in workspace.runs[:12]
        ],
        "artifacts": [
            {"kind": artifact.kind, "file_url": artifact.file_url}
            for artifact in workspace.artifacts
        ],
    }


async def run_controller_turn(
    session: AsyncSession,
    runtime: AgentRuntime,
    controller_session: ControllerSession,
    message: str,
    *,
    search: SearchProvider,
    history: list[tuple[str, str]] | None = None,
    emit: Callable[[dict], Awaitable[None]] | None = None,
) -> ControllerTurn:
    if not runtime.settings.openai_api_key:
        raise ControllerUnavailable("没有 OPENAI_API_KEY，总控不可用；请先在 backend/.env 配置。")

    async def notify(event: dict) -> None:
        if emit is not None:
            await emit(event)

    product = (
        await session.get(ProductProfile, controller_session.product_id)
        if controller_session.product_id
        else None
    )
    batch = await session.get(Batch, controller_session.batch_id) if controller_session.batch_id else None
    draft = (
        ResearchDraft.model_validate(controller_session.draft_json)
        if controller_session.draft_json
        else None
    )
    deps = ControllerDeps(
        session=session,
        runtime=runtime,
        settings=runtime.settings,
        search=search,
        product=product,
        batch=batch,
        draft=draft,
    )

    model = build_pydantic_model(runtime.settings)
    agent = Agent(
        model,
        output_type=str,
        deps_type=ControllerDeps,
        model_settings=build_model_settings(runtime.settings, temperature=0.3),
        instructions=(
            "你是「智农云链」的总控，不是内容生成 Agent。"
            "你可以读取产品/批次/AgentRun，调用四个 Agent，或启动调研。"
            "用户要新产品的资料时先调 research_product；有草案后向用户列缺口。"
            "危险动作（建档、通过、驳回、回退）只能调 request_action 让用户确认，绝不能直接执行。"
            "用户说包装/故事不好时，调 run_agent 并带上具体 note；如果目标站已通过且下游存在，改调 request_action('rewind_to_agent')。"
            "只调用必要工具，同一工具不要连续重复；拿到足够信息后直接回答。"
            "批次状态为 traced 时说明四站已完成、可看溯源/新批次，不要编造“最后确认/上架”等不存在的步骤。"
            "只有确实调用了 request_action 时才提确认；不要把普通查询说成危险动作。"
            "最终回答用中文自然语言，直接给结论和下一步；不要输出 JSON、代码围栏或 final_result 字样。"
            "回答用纯文本，不要用 Markdown 加粗、标题；需要分点就用「-」。"
            "需要用户补充信息时，在回答里列 1–3 个具体问题。"
            "工具失败时如实说明原因和替代做法，不要编造检索结果。"
        ),
    )

    @agent.tool
    async def list_products(ctx: RunContext[ControllerDeps]) -> list[dict]:
        """List active products and their ids/slugs."""
        rows = (
            await ctx.deps.session.execute(
                select(ProductProfile)
                .where(ProductProfile.is_active.is_(True))
                .order_by(ProductProfile.id)
            )
        ).scalars()
        return [
            {
                "id": item.id,
                "slug": item.slug,
                "name": item.name,
                "county": item.county,
                "form": item.form,
            }
            for item in rows
        ]

    @agent.tool
    async def get_workspace(ctx: RunContext[ControllerDeps]) -> dict:
        """Read current batch state, recent runs, and artifacts."""
        if ctx.deps.batch is None:
            return {"error": "当前没有选中批次"}
        workspace = await load_workspace(ctx.deps.session, ctx.deps.batch.id)
        if workspace is None:
            return {"error": "批次不存在"}
        return _workspace_summary(workspace)

    @agent.tool
    async def research_product(ctx: RunContext[ControllerDeps], brief: str) -> dict:
        """Search sources and build a product/knowledge draft. May ask follow-up questions."""
        try:
            draft = await run_research(
                brief,
                settings=ctx.deps.settings,
                search=ctx.deps.search,
                known={
                    "current_product": ctx.deps.product.name
                    if ctx.deps.product is not None
                    else "",
                },
            )
        except ResearchUnavailable as exc:
            return {"error": str(exc)}
        ctx.deps.draft = draft
        return {
            "product": draft.product.model_dump(),
            "doc_count": len(draft.docs),
            "benchmark_count": len(draft.benchmarks),
            "questions": draft.questions,
            "warnings": draft.warnings,
            "sources": [item.model_dump() for item in draft.sources],
        }

    @agent.tool
    async def run_agent(
        ctx: RunContext[ControllerDeps], agent: str, note: str = ""
    ) -> dict:
        """Run or revise one of story/packaging/marketing/pricing."""
        if ctx.deps.batch is None:
            return {"error": "当前没有选中批次"}
        try:
            target = AgentName(agent)
        except ValueError:
            return {"error": f"未知 Agent: {agent}"}
        current = STAGE_INDEX.get(ctx.deps.batch.state, -1)
        target_index = AGENT_ORDER.index(target)
        if current > target_index:
            return {
                "error": "目标站已通过且下游存在，需要先确认回退",
                "suggest": "request_action:rewind_to_agent",
            }
        if current < target_index:
            return {"error": f"当前还不到 {agent} 站"}
        try:
            from .orchestrator import run_agent as run_pipeline_agent

            run = await run_pipeline_agent(
                ctx.deps.session, ctx.deps.batch, target, ctx.deps.runtime, note or None
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:500]}
        return {
            "agent": target.value,
            "status": run.status,
            "model": run.model,
            "tokens": run.tokens,
            "output_preview": _summary_output(run.output_json),
        }

    @agent.tool
    async def request_action(
        ctx: RunContext[ControllerDeps],
        kind: str,
        summary: str,
        agent: str = "",
        note: str = "",
    ) -> dict:
        """Create a pending action for user confirmation; does not execute it."""
        allowed = {"commit_product", "approve_agent", "reject_agent", "rewind_to_agent"}
        if kind not in allowed:
            return {"error": f"不允许的动作: {kind}"}
        pending = {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "summary": summary,
            "agent": agent,
            "note": note,
        }
        ctx.deps.pending = pending
        return {"pending": pending, "message": "已生成确认卡，等待用户确认。"}

    context = {
        "product": (
            {"id": product.id, "slug": product.slug, "name": product.name, "county": product.county}
            if product
            else None
        ),
        "batch": (
            {"id": batch.id, "code": batch.code, "state": batch.state, "trace_code": batch.trace_code}
            if batch
            else None
        ),
        "draft": (
            {
                "product": draft.product.model_dump(),
                "doc_count": len(draft.docs),
                "questions": draft.questions,
                "warnings": draft.warnings,
            }
            if draft
            else None
        ),
    }
    transcript = "\n".join(f"{role}: {content}" for role, content in (history or [])[-12:])
    prompt = f"""当前上下文：
{json.dumps(context, ensure_ascii=False)}

最近对话：
{transcript or "（无）"}

用户消息：
{message}
"""
    text_chunks: list[str] = []
    thinking_chunks: list[str] = []
    result = None
    try:
        async with agent.run_stream_events(
            prompt,
            deps=deps,
            usage_limits=UsageLimits(
                request_limit=runtime.settings.controller_request_limit,
                tool_calls_limit=runtime.settings.controller_tool_calls_limit,
            ),
        ) as events:
            async for event in events:
                if isinstance(event, AgentRunResultEvent):
                    result = event.result
                elif isinstance(event, PartStartEvent):
                    part = event.part
                    if isinstance(part, ThinkingPart) and part.content:
                        thinking_chunks.append(part.content)
                        await notify({"type": "thinking", "text": part.content})
                    elif isinstance(part, TextPart) and part.content:
                        text_chunks.append(part.content)
                        await notify({"type": "delta", "text": part.content})
                elif isinstance(event, PartDeltaEvent):
                    delta = event.delta
                    if isinstance(delta, ThinkingPartDelta) and delta.content_delta:
                        thinking_chunks.append(delta.content_delta)
                        await notify({"type": "thinking", "text": delta.content_delta})
                    elif isinstance(delta, TextPartDelta) and delta.content_delta:
                        text_chunks.append(delta.content_delta)
                        await notify({"type": "delta", "text": delta.content_delta})
                elif isinstance(event, FunctionToolCallEvent):
                    name = event.part.tool_name
                    deps.events.append({"tool": name, "status": "running"})
                    await notify({"type": "tool", "name": name, "status": "running"})
                elif isinstance(event, FunctionToolResultEvent):
                    name = str(getattr(event.part, "tool_name", "") or "")
                    deps.events.append({"tool": name, "status": "done"})
                    await notify({"type": "tool", "name": name, "status": "done"})
    except Exception as exc:
        raise ControllerUnavailable(f"总控调用失败：{str(exc)[:240]}") from exc

    reply_text = (result.output if result is not None else "").strip()
    if not reply_text:
        reply_text = "".join(text_chunks).strip()
    if not reply_text:
        raise ControllerUnavailable("总控没有生成文字回复，请再试一次。")

    return ControllerTurn(
        reply=reply_text,
        draft=deps.draft,
        pending=deps.pending,
        events=deps.events,
        questions=list(deps.draft.questions) if deps.draft else [],
        thinking=_thinking_lines("".join(thinking_chunks)),
    )
