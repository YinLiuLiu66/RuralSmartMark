from __future__ import annotations

import json
import re
from typing import Any

from ..agents.runtime import AgentRuntime
from ..schemas import TraceChatOut, TraceOut
from .fact_guard import find_banned_claim

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

_SYSTEM = """你是县域农产品溯源页里的 IP 对话角色。只使用我给出的事实包回答消费者。
硬性规则：
1. 不编年份、产量、人物、检测值、认证或价格；事实包没有的就说“这一页没有记录”。
2. 不写医疗/保健功效；不声称有机、绿色食品、富硒、无公害、官方认证或地理标志授权。
3. 不承诺甜度、增收、售罄或口感；不写绝对化表述。
4. 回答 60–160 个汉字，用中文，口语、克制，不要 Markdown，不要反问太多。
5. 涉及演示品牌、IP、合作社、价格时，要点明“演示”。
"""


def _numbers(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            found.update(_numbers(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_numbers(item))
    elif isinstance(value, str):
        found.update(_NUMBER.findall(value))
    return found


def _allowed_numbers(trace: TraceOut) -> set[str]:
    payload = {
        "batch_code": trace.batch.code,
        "quantity_kg": trace.batch.quantity_kg,
        "specs": trace.product.specs,
        "story": {
            "story_long": trace.story.story_long,
            "story_short": trace.story.story_short,
            "taglines": trace.story.taglines,
        },
        "packaging": {
            "concept": trace.packaging.concept,
            "copy": trace.packaging.packaging_copy.model_dump(),
            "structure": trace.packaging.structure,
        },
        "pricing": {
            "price_ladder": [item.model_dump() for item in trace.pricing.price_ladder],
            "premium_pct": trace.pricing.premium_pct,
            "rationale": trace.pricing.rationale,
            "formula": trace.pricing.formula,
            "faq": [item.model_dump() for item in trace.pricing.faq],
        },
    }
    return _numbers(payload)


def _safe_refusal(issue_rule: str, trace: TraceOut) -> str | None:
    if issue_rule == "COMP-03":
        return (
            "这属于医疗或保健方面的问题，我不能给出这样的结论。"
            f"这里只讲这一批{trace.product.name}的产地、包装、价格和保存方式。"
        )
    if issue_rule in {"COMP-02", "COMP-06"}:
        return (
            "我们没有相关认证证书，也不声称官方授权或地理标志授权。"
            f"这里只把{trace.product.county}作为产地背景，品牌与角色均为演示设定。"
        )
    if issue_rule == "COMP-04":
        return "我不能对口感、销售或增收做保证。这一页只说明批次记录和演示测算，不替任何一颗果子打包票。"
    if issue_rule == "STYLE-02":
        return (
            "冰糖心是个别果子的偶然情况，不能说每颗都有。挑果时看果径和外观，页面不把偶然写成保证。"
        )
    return None


def _faq(trace: TraceOut, *keywords: str) -> str | None:
    for item in trace.pricing.faq:
        if any(keyword in item.q for keyword in keywords):
            return item.a
    return None


def _template_reply(message: str, trace: TraceOut) -> str:
    text = message.strip()
    if any(keyword in text for keyword in ("贵", "价格", "溢价", "多少钱", "128", "元")):
        return f"{trace.pricing.rationale} 以上是演示测算。"
    if any(keyword in text for keyword in ("斑点", "丑", "表皮", "外观", "果皮", "果粉", "白霜")):
        return (
            f"{trace.packaging.packaging_copy.back} "
            f"这是演示合作社的设定，不是{trace.product.name}全行业的样子。"
        )
    if any(keyword in text for keyword in ("保存", "放多久", "冷藏", "储存")):
        return (
            _faq(trace, "保存", "放") or "阴凉通风处保存，冷藏口感更脆；按批次标注的时间尽快食用。"
        )
    aliases = trace.product.specs.get("origin_aliases") or []
    if not isinstance(aliases, list):
        aliases = []
    if any(
        keyword in text
        for keyword in ("产地", "哪里", "海拔", "果园", trace.product.name, *aliases)
    ):
        return (
            f"这一批来自{trace.product.county}。"
            f"{trace.story.story_short} 具体海拔没有核定，这一页不写。"
        )
    if any(keyword in text for keyword in ("甜", "酸", "好吃", "口感", "糖")):
        sugar = str(trace.product.specs.get("sugar") or "")
        return (
            "甜不甜、酸不酸要看这一颗的实际口感，我不能替每颗果子担保。"
            f"产品档案里的口径是：{sugar}；那是资料口径，不是单颗实测值。"
        )
    if any(keyword in text for keyword in ("码", "批次", "溯源", "真的", "记录")):
        return (
            f"这一批的批次码是 {trace.batch.code}，溯源码是 {trace.trace_code}。"
            "故事、包装、内容和定价都经过人工审核，价格与角色均为演示。"
        )
    if any(keyword in text for keyword in ("谁", "IP", "守园人", "角色")):
        return trace.story.persona
    return (
        f"我是{trace.story.ip_name}。这一页只记录这一批有据可查的事："
        f"{trace.story.story_short} 你可以问我产地、包装、价格或保存。"
    )


async def answer_trace_question(
    runtime: AgentRuntime, trace: TraceOut, message: str
) -> TraceChatOut:
    text = message.strip()
    issue = find_banned_claim(text)
    if issue is not None:
        refusal = _safe_refusal(issue.rule, trace)
        if refusal:
            return TraceChatOut(reply=refusal, source="template")

    fallback = _template_reply(text, trace)
    if runtime.provider_name == "mock":
        return TraceChatOut(reply=fallback, source="template")

    facts = {
        "product": trace.product.model_dump(),
        "batch": trace.batch.model_dump(mode="json"),
        "story": trace.story.model_dump(),
        "packaging": trace.packaging.model_dump(),
        "pricing": trace.pricing.model_dump(),
        "evidence": [item.model_dump() for item in trace.story.evidence],
    }
    prompt = (
        f"事实包：\n{json.dumps(facts, ensure_ascii=False)}\n\n"
        f"消费者问题：{text}\n"
        "请直接回答，不要输出 JSON。"
    )
    try:
        response = await runtime.llm.complete(_SYSTEM, prompt, temperature=0.4)
        reply = response.text.strip()
    except Exception:  # noqa: BLE001 - provider failures degrade to a safe template reply
        return TraceChatOut(reply=fallback, source="template")

    if not reply or reply.startswith("{"):
        return TraceChatOut(reply=fallback, source="template")
    if find_banned_claim(reply) is not None:
        return TraceChatOut(reply=fallback, source="template")
    if _numbers(reply) - _allowed_numbers(trace):
        return TraceChatOut(reply=fallback, source="template")
    return TraceChatOut(reply=reply[:400], source="llm")
