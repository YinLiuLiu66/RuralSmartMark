from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ..models import KnowledgeDoc
from .knowledge import docs_number_tokens

Severity = Literal["error", "warning"]

_NUMBER_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(万亩|万吨|亿元|万户|万人|千克|公斤|kg|g|米|m|%|年|元/斤|元/kg|元|枚|mm|厘米|小时|天)"
)
_SKIP_KEYS = {"doc_id", "quote", "source_url", "qr_payload", "fallback_reason"}

_BANNED_RULES: list[tuple[str, re.Pattern[str], Severity, str]] = [
    (
        "COMP-02",
        re.compile(r"有机|绿色食品|富硒|无公害"),
        "error",
        "未提供认证证书，不得出现有机/绿色食品/富硒/无公害等认证表述",
    ),
    (
        "COMP-03",
        re.compile(
            r"降血糖|降血脂|降血压|降糖|治疗|治愈|疗效|抗癌|防癌|增强免疫|提高免疫|"
            r"排毒|养颜|保健功效|药效|助眠"
        ),
        "error",
        "普通食品不得写医疗/保健功效",
    ),
    (
        "COMP-04",
        re.compile(r"保证(?:增收|卖完|甜|好吃|品质|正宗)|稳赚|包销|不愁卖|百分百|100%甜"),
        "error",
        "不得写增收/销售/口感保证",
    ),
    (
        "COMP-06",
        re.compile(
            r"已获(?:得)?地理标志授权|获得地理标志授权|地理标志授权产品|"
            r"授权使用地理标志|政府指定|官方认证|官方推荐|官方授权"
        ),
        "error",
        "不得暗示官方授权或背书",
    ),
    (
        "COMP-07",
        re.compile(r"传说|祖传|三百年|千年|世代守护|神秘起源"),
        "warning",
        "文化表述必须是可查意象，不得编造历史渊源",
    ),
    (
        "STYLE-01",
        re.compile(r"最大|最好|最强|第一|唯一|顶级|首选|天花板"),
        "warning",
        "绝对化表述需人工确认；没有来源就改弱",
    ),
    (
        "STYLE-02",
        re.compile(r"个个冰糖心|每颗都有冰糖心|颗颗冰糖心"),
        "error",
        "冰糖心不是每颗都有，禁止绝对化",
    ),
]


@dataclass(slots=True)
class GuardIssue:
    rule: str
    field: str
    message: str
    severity: Severity
    suggestion: str = ""


@dataclass(slots=True)
class GuardResult:
    errors: list[GuardIssue] = field(default_factory=list)
    warnings: list[GuardIssue] = field(default_factory=list)
    checked_citations: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def add(
        self,
        rule: str,
        field_path: str,
        message: str,
        severity: Severity,
        suggestion: str = "",
    ) -> None:
        issue = GuardIssue(
            rule=rule,
            field=field_path,
            message=message,
            severity=severity,
            suggestion=suggestion,
        )
        if severity == "error":
            self.errors.append(issue)
        else:
            self.warnings.append(issue)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked_citations": self.checked_citations,
            "errors": [asdict(item) for item in self.errors],
            "warnings": [asdict(item) for item in self.warnings],
        }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def _negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 8) : start]
    return any(marker in prefix for marker in ("不", "非", "无", "未", "没有", "不含"))


def find_banned_claim(text: str, *, include_warnings: bool = False) -> GuardIssue | None:
    """Return the first unsafe claim in free text, e.g. a chat reply."""
    for rule, pattern, severity, message in _BANNED_RULES:
        if severity == "warning" and not include_warnings:
            continue
        for match in pattern.finditer(text):
            if _negated(text, match.start()):
                continue
            return GuardIssue(
                rule=rule,
                field="<text>",
                message=f"{message}：{match.group(0)}",
                severity=severity,
                suggestion="改写为可验证、有限定的表述",
            )
    return None


def _walk_strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _SKIP_KEYS:
                continue
            child = f"{path}.{key}" if path else str(key)
            found.extend(_walk_strings(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk_strings(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        found.append((path or "<root>", value))
    return found


def _citation_items(data: dict) -> list[dict]:
    items = data.get("cultural_evidence") or data.get("fact_refs") or []
    return [item for item in items if isinstance(item, dict)]


def check_output(
    data: dict,
    docs: list[KnowledgeDoc],
    *,
    allowed_numbers: set[str] | None = None,
) -> GuardResult:
    result = GuardResult()
    docs_by_key = {doc.doc_key: doc for doc in docs}

    citations = _citation_items(data)
    if not citations:
        result.add(
            "CRIT-00",
            "citations",
            "至少需要一条知识库引用",
            "error",
            "从知识库选择一条原文，填入 cultural_evidence/fact_refs",
        )

    for index, citation in enumerate(citations):
        doc_id = str(citation.get("doc_id", ""))
        quote = str(citation.get("quote", ""))
        field_path = f"citations[{index}]"
        doc = docs_by_key.get(doc_id)
        if doc is None:
            result.add(
                "CRIT-01",
                field_path,
                f"引用的 doc_id 不存在: {doc_id}",
                "error",
                "只能引用下列 doc_id：" + "、".join(sorted(docs_by_key)),
            )
            continue

        result.checked_citations += 1
        if quote and _normalize(quote) not in _normalize(doc.content):
            result.add(
                "CRIT-02",
                field_path,
                f"引用文字未在 {doc_id} 正文中逐字出现",
                "error",
                "从知识库原文复制一句话，不要改写、不要加省略号",
            )
        if doc.credibility == "demo":
            result.add(
                "DEMO-01",
                field_path,
                f"{doc_id} 是演示设定，不是事实来源",
                "warning",
                "界面必须标注“演示”；不要把演示设定写成区域事实",
            )
        elif doc.credibility == "todo":
            result.add(
                "CRIT-03",
                field_path,
                f"{doc_id} 仍是待核验条目",
                "error",
                "先用 seed 更新知识库，或改引已核验条目",
            )
        if not doc.source_url or doc.source_url.upper().startswith("TODO"):
            result.add(
                "CRIT-04",
                field_path,
                f"{doc_id} 缺少 source_url",
                "warning",
                "补来源后再当作事实引用",
            )

    cited_ids = {str(item.get("doc_id", "")) for item in citations if item.get("doc_id")}
    cited_docs = [doc for doc in docs if doc.doc_key in cited_ids]
    allowed = set(allowed_numbers or set())
    allowed.update(docs_number_tokens(cited_docs or docs))

    for field_path, text in _walk_strings(data):
        # 客服问答的 q 是提问，不是对外宣称；只校验回答和正文。
        if not field_path.endswith(".q"):
            for rule, pattern, severity, message in _BANNED_RULES:
                for match in pattern.finditer(text):
                    if _negated(text, match.start()):
                        continue
                    result.add(
                        rule,
                        field_path,
                        f"{message}：{match.group(0)}",
                        severity,
                        "改写为可验证、有限定的表述",
                    )

            if ("不套袋" in text or "不打蜡" in text) and "DEMO-01" not in cited_ids:
                result.add(
                    "DEMO-02",
                    field_path,
                    "“不套袋/不打蜡”是演示合作社设定，但产出没有引用 DEMO-01",
                    "error",
                    "引用 DEMO-01 并标注演示，或删除这句话",
                )

        if field_path.endswith("formula"):
            continue
        for match in _NUMBER_PATTERN.finditer(text):
            token = match.group(1)
            if token in allowed:
                continue
            result.add(
                "NUM-01",
                field_path,
                f"数字 {match.group(0)} 未在引用文档或产品档案中找到",
                "warning",
                "人工确认口径；没有来源就删掉或改成定性表述",
            )

    return result


def format_guard_for_prompt(result: GuardResult) -> str:
    lines: list[str] = []
    for issue in result.errors:
        lines.append(f"- [{issue.rule}] {issue.field}: {issue.message}（{issue.suggestion}）")
    for issue in result.warnings:
        lines.append(f"- [提示/{issue.rule}] {issue.field}: {issue.message}")
    return "\n".join(lines) if lines else "无问题"
