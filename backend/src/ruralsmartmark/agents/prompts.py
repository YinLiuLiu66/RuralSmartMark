from __future__ import annotations

import json
from typing import Any

from ..models import Batch, KnowledgeDoc, ProductProfile
from ..services.knowledge import format_docs_for_prompt
from .base import AgentName

_DEFAULT_CONTEXT = "云南昭通昭阳区的丑苹果，以及一个虚构的合作社子品牌「乌蒙丑果」"
_DEFAULT_BRAND_RULE = (
    "品牌名固定为「乌蒙丑果」，IP 名固定为「山风守园人」；不得另起名，也不得把 IP 写成真实人物。"
)
_DEFAULT_DEMO_RULE = (
    "合作社、品牌、果农人物、批次数据是演示合成；引用 DEMO-01 时，内容只是在说明“这是演示”，"
    "不能反过来当作产地事实。\n"
    "   写到年份/产量/产值/户数时引用 ORIGIN-01；写品质指标时引用 ENV-01；"
    "写种植历史时引用 CUL-01。数字找不到引用就不要写。\n"
    "   任何字段只要出现“不套袋/不打蜡”，fact_refs / cultural_evidence 必须包含 DEMO-01，"
    "并写明这是演示合作社设定；做不到就删掉这句话。"
)
_DEFAULT_GI_RULE = "不冒充“昭通苹果”地理标志授权，只把区域品牌作为产地背景。"
_GENERIC_DEMO_RULE = (
    "合作社、品牌、人物、批次数据是演示合成；引用 DEMO-01 时，内容只是在说明“这是演示”，"
    "不能反过来当作产地事实。\n"
    "   写到年份/产量/产值/户数、品质指标、种植历史时，必须引用知识库中对应 doc；"
    "数字找不到引用就不要写。\n"
    "   任何字段只要涉及演示设定，fact_refs / cultural_evidence 必须包含 DEMO-01。"
)
_GENERIC_GI_RULE = "不冒充任何地理标志授权，只把区域品牌作为产地背景。"
_ZHAOTONG_SLUG = "zhaotong-ugly-apple"

_DEFAULT_BRIEFS = {
    AgentName.STORY: (
        "你是乡土故事挖掘机。任务：给这个批次一个可持续使用的 IP 名称、人格、长故事、短故事、"
        "三条以内标签和引用证据。故事要具体、克制、有山野气，不卖惨、不编传说。"
        "story_long 写 300–600 个汉字，story_short 写 12–30 个汉字。"
        "ip_name 必须逐字写「山风守园人」；persona 写守园人视角（演示合成的角色），不要写成真实人物或真实果农。"
        "“不套袋/不打蜡”只能写成演示合作社的设定，并且必须引用 DEMO-01；"
        "不能把它写成昭通苹果全行业的事实。"
        "写“2024/产量/产值/户数”必须引用 ORIGIN-01；写糖度/硬度引用 ENV-01。"
    ),
    AgentName.PACKAGING: (
        "你是包装设计智能体。任务：基于已通过的故事，给出一个可落地的 5kg/12 枚礼盒方案："
        "概念、色板、字体、正面/背面/侧面/盒内文案、结构、成本估算、衍生品建议。"
        "文案要短，能放进版面；成本 total 必须等于 box+tray+print。"
    ),
    AgentName.MARKETING: (
        "你是农产品营销官。任务：基于故事与包装，产出小红书、抖音、朋友圈三套内容，"
        "以及客服问答和 KOL Brief。语气与 IP 一致；不写功效、不写绝对化承诺。"
        "内容里出现“不套袋/不打蜡”时，fact_refs 必须包含 DEMO-01（quote 逐字复制）并点明演示设定；"
        "fact_refs 至少一条，写区域数字/品质指标时分别引用 ORIGIN-01 / ENV-01。"
    ),
    AgentName.PRICING: (
        "你是溢价核算与溯源 Agent。价格数字由确定性计算器给出，你的任务只是把数字解释清楚，"
        "并写欢迎语与常见问题；不得改动价格、毛利、溢价率。"
    ),
}


def _spec(product: ProductProfile, key: str, default: str) -> str:
    value = (product.specs or {}).get(key)
    return str(value).strip() if value else default


def _brand_name(product: ProductProfile) -> str:
    return _spec(product, "brand_name", f"{product.name}演示品牌")


def _ip_name(product: ProductProfile) -> str:
    return _spec(product, "ip_name", "山野记录者")


def _is_zhaotong(product: ProductProfile) -> bool:
    return product.slug == _ZHAOTONG_SLUG


def _product_brief(agent: AgentName, product: ProductProfile) -> str:
    brand = _brand_name(product)
    ip = _ip_name(product)
    if agent == AgentName.STORY:
        return (
            "你是乡土故事挖掘机。任务：给这个批次一个可持续使用的 IP 名称、人格、长故事、"
            "短故事、三条以内标签和引用证据。故事要具体、克制、有山野气，不卖惨、不编传说。"
            "story_long 写 300–600 个汉字，story_short 写 12–30 个汉字。"
            f"ip_name 必须逐字写「{ip}」；品牌为「{brand}」。"
            "persona 写这一产品/产地的品牌角色（演示合成），不要写成真实人物或真实果农。"
            f"只能使用{product.name}的知识库；不得出现其他产品的品牌、IP、产地或事实。"
        )
    if agent == AgentName.PACKAGING:
        return (
            f"你是包装设计智能体。任务：基于已通过的故事，为{product.name}（{product.form}）"
            "给出一个可落地的礼盒方案：概念、色板、字体、正面/背面/侧面/盒内文案、结构、"
            "成本估算、衍生品建议。"
            f"品牌「{brand}」，IP「{ip}」。文案要短，能放进版面；"
            "成本 total 必须等于 box+tray+print。"
        )
    if agent == AgentName.MARKETING:
        return (
            f"你是农产品营销官。任务：基于{product.name}的故事与包装，产出小红书、抖音、"
            "朋友圈三套内容，以及客服问答和 KOL Brief。"
            f"品牌「{brand}」，IP「{ip}」；语气与 IP 一致；不写功效、不写绝对化承诺。"
            "fact_refs 至少一条，引用必须来自本产品知识库；"
            "不得出现其他产品的品牌、IP、产地或事实。"
        )
    return (
        f"你是溢价核算与溯源 Agent。价格数字由确定性计算器给出，你的任务只是把"
        f"{product.name}的价格解释清楚，并写欢迎语与常见问题；"
        "不得改动价格、毛利、溢价率，不得使用其他产品事实。"
    )


def build_system_prompt(product: ProductProfile) -> str:
    brand = _brand_name(product)
    ip = _ip_name(product)
    if _is_zhaotong(product):
        context = _spec(product, "agent_context", _DEFAULT_CONTEXT)
        brand_rule = _spec(product, "brand_rule", _DEFAULT_BRAND_RULE)
        demo_rule = _spec(product, "demo_claim_rule", _DEFAULT_DEMO_RULE)
        gi_rule = _spec(product, "gi_claim_rule", _DEFAULT_GI_RULE)
    else:
        context = _spec(
            product,
            "agent_context",
            f"{product.county}的{product.name}，以及一个虚构的合作社子品牌「{brand}」",
        )
        brand_rule = _spec(
            product,
            "brand_rule",
            f"品牌名固定为「{brand}」，IP 名固定为「{ip}」；不得另起名，也不得把 IP 写成真实人物。",
        )
        demo_rule = _spec(product, "demo_claim_rule", _GENERIC_DEMO_RULE)
        gi_rule = _spec(product, "gi_claim_rule", _GENERIC_GI_RULE)
    return f"""你是「智农云链」县域农产品品牌数字化重构系统里的专业 Agent。
你的工作对象是{context}。
{brand_rule}

硬性规则：
1. 只能把知识库中明确写出的事实当作事实；知识库没有的数字、人物、认证、年份，不要写。
2. cultural_evidence / fact_refs 里的 quote 必须从知识库正文逐字复制一句话，不能改写、不能加省略号；doc_id 必须存在。
3. 不得写“有机、绿色食品、富硒、无公害”等未提供证书的认证；不得写医疗/保健功效；不得写保证增收/保证卖完/个个冰糖心。
4. {demo_rule}
5. {gi_rule}
6. 价格由系统计算，你不负责编价格；你只写与已给数字一致的解释。
7. 只输出一个 JSON 对象，不要 Markdown、不要解释、不要输出 JSON 以外的文字。
"""


def agent_brief(agent: AgentName, product: ProductProfile) -> str:
    custom = _spec(product, f"{agent.value}_brief", "")
    if custom:
        return custom
    if _is_zhaotong(product):
        return _DEFAULT_BRIEFS[agent]
    return _product_brief(agent, product)


def _schema_text(schema: dict) -> str:
    return json.dumps(schema, ensure_ascii=False, separators=(",", ":"))


def _upstream_text(outputs: dict[str, Any]) -> str:
    if not outputs:
        return "（无上游产出）"
    blocks = []
    for name, value in outputs.items():
        if value:
            blocks.append(f"### {name}\n{json.dumps(value, ensure_ascii=False, indent=2)}")
    return "\n\n".join(blocks) if blocks else "（无上游产出）"


def build_agent_prompt(
    agent: AgentName,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    outputs: dict[str, Any],
    note: str | None,
    schema: dict,
    *,
    feedback: str | None = None,
) -> str:
    note_text = note.strip() if note and note.strip() else "（无额外修改要求）"
    feedback_text = feedback.strip() if feedback else ""
    return f"""{agent_brief(agent, product)}

## 产品档案
名称：{product.name}
产地：{product.county}
形态：{product.form}
规格：{json.dumps(product.specs, ensure_ascii=False)}
品牌边界：{product.specs.get("positioning", "虚构合作社子品牌，演示合成")}

## 当前批次
批次码：{batch.code}
数量：{batch.quantity_kg:g} kg
状态：{batch.state}

## 知识库（只能引用这些 doc_id）
{format_docs_for_prompt(docs)}

## 上游已通过产出
{_upstream_text(outputs)}

## 本次修改要求
{note_text}

## 输出 JSON Schema
{_schema_text(schema)}

请直接输出满足 Schema 的 JSON 对象。引用必须逐字来自知识库；不确定的内容删掉，不要补。
{f"## 上一次输出未通过校验，请修复{chr(10)}{feedback_text}" if feedback_text else ""}
"""


def build_pricing_narrative_prompt(base: dict[str, Any], allowed_numbers: set[str]) -> str:
    numbers = "、".join(sorted(allowed_numbers, key=lambda item: (len(item), item)))
    return f"""下面是系统已经算好的定价结果。请只写三部分解释：
- rationale：120–220 字，说明基线、礼盒价、成本与毛利，必须明确“演示测算”。
- persona_greeting：30–80 字，用 IP 人格欢迎扫码者。
- faq：3 条问答，回答价格差异、外观/品相差异、保存方式；只按该产品的实际形态写，不套用其它品类。

允许出现的数字只有：{numbers}
不得新增、修改或四舍五入这些数字；不得写保证增收/保证卖完/有机/绿色食品/富硒/功效。
只输出 JSON，字段为 rationale、persona_greeting、faq（数组，元素含 q、a）。

定价结果：
{json.dumps(base, ensure_ascii=False, indent=2)}
"""
