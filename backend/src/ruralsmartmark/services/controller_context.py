"""页面上下文解析（decisions #92）。

总控是全局唯一会话，每条消息带前端当前页面。这里负责把 slug / batch_id
解析成 ORM 对象并校验归属，非法输入一律抛中文错误，不静默降级。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Batch, ProductProfile
from ..schemas import ControllerPageContext


class PageContextError(ValueError):
    """页面上下文非法（产品/批次不存在或不属于同一产品）。"""


class PendingTargetError(ValueError):
    """确认卡缺少目标或目标已变化。"""


@dataclass(slots=True)
class ResolvedPageContext:
    route: str | None = None
    focus_agent: str | None = None
    product: ProductProfile | None = None
    batch: Batch | None = None

    @property
    def label(self) -> str:
        """历史消息里用的短标签，如「昭通丑苹果 / ZT-DEMO-001」。"""
        parts = []
        if self.product is not None:
            parts.append(self.product.name)
        if self.batch is not None:
            parts.append(self.batch.code)
        return " / ".join(parts)

    def as_dict(self) -> dict:
        return {
            "route": self.route,
            "focus_agent": self.focus_agent,
            "product": {
                "id": self.product.id,
                "slug": self.product.slug,
                "name": self.product.name,
            }
            if self.product
            else None,
            "batch": {
                "id": self.batch.id,
                "code": self.batch.code,
                "state": self.batch.state,
            }
            if self.batch
            else None,
        }


async def resolve_page_context(
    session: AsyncSession, context: ControllerPageContext | None
) -> ResolvedPageContext:
    if context is None:
        return ResolvedPageContext()

    product: ProductProfile | None = None
    if context.product_slug:
        product = await session.scalar(
            select(ProductProfile).where(ProductProfile.slug == context.product_slug)
        )
        if product is None:
            raise PageContextError("页面上的产品不存在，可能已被删除，请回到工作台重新进入")

    batch: Batch | None = None
    if context.batch_id is not None:
        batch = await session.get(Batch, context.batch_id)
        if batch is None:
            raise PageContextError("页面上的批次不存在，可能已被删除，请重新选择批次")

    if batch is not None:
        if product is not None and batch.product_id != product.id:
            raise PageContextError("页面上的批次不属于该产品，请重新进入项目页")
        if product is None:
            product = await session.get(ProductProfile, batch.product_id)

    return ResolvedPageContext(
        route=context.route,
        focus_agent=context.focus_agent,
        product=product,
        batch=batch,
    )


def history_content(action_json: dict | None, content: str) -> str:
    """给历史 user 消息补页面标签，避免全局会话里旧消息失去归属。"""
    if not action_json:
        return content
    label = action_json.get("page_label")
    if not label:
        return content
    return f"【页面：{label}】{content}"


def draft_hash(data: dict | None) -> str | None:
    """草案内容哈希：确认卡用它判断草案是否已被新的录入覆盖。"""
    if not data:
        return None
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def pending_batch(session: AsyncSession, pending: dict) -> Batch:
    """按确认卡冻结的 batch_id 取批次，并校验状态未被改动。"""
    batch_id = pending.get("batch_id")
    if not batch_id:
        raise PendingTargetError("确认卡缺少批次目标，请回到项目页重新发起")
    batch = await session.get(Batch, int(batch_id))
    if batch is None:
        raise PendingTargetError("确认卡里的批次已被删除，请重新发起")

    frozen_state = pending.get("batch_state")
    if frozen_state and frozen_state != batch.state:
        raise PendingTargetError(
            f"批次状态已变化（出卡时 {frozen_state}，现在 {batch.state}），请重新发起"
        )

    # 时间戳只做宽松校验：SQLite 秒级精度，跨库/时区容易出现误报。
    frozen_at = _parse_datetime(pending.get("batch_updated_at"))
    if frozen_at is not None and batch.updated_at is not None:
        try:
            drift = abs((batch.updated_at - frozen_at).total_seconds())
        except TypeError:
            drift = 0
        if drift > 1:
            raise PendingTargetError("批次在出卡后已被其它操作改动，请重新发起")
    return batch


async def pending_product(session: AsyncSession, pending: dict) -> ProductProfile:
    product_id = pending.get("product_id")
    if not product_id:
        raise PendingTargetError("确认卡缺少产品目标，请回到项目页重新发起")
    product = await session.get(ProductProfile, int(product_id))
    if product is None:
        raise PendingTargetError("确认卡里的产品已被删除，请重新发起")
    return product


async def target_candidates(
    session: AsyncSession, product: ProductProfile | None
) -> list[dict]:
    """没有页面批次时给前端/模型的候选：优先该产品下的批次，否则列产品。"""
    if product is not None:
        rows = (
            await session.execute(
                select(Batch).where(Batch.product_id == product.id).order_by(Batch.id.desc())
            )
        ).scalars()
        return [
            {
                "kind": "batch",
                "product_slug": product.slug,
                "batch_id": item.id,
                "code": item.code,
                "state": item.state,
                "label": f"{product.name} / {item.code}",
            }
            for item in rows
        ]

    products = (
        await session.execute(
            select(ProductProfile)
            .where(ProductProfile.is_active.is_(True))
            .order_by(ProductProfile.id)
        )
    ).scalars()
    return [
        {
            "kind": "product",
            "product_slug": item.slug,
            "product_id": item.id,
            "label": f"{item.name}（{item.county}）",
            "hint": "进入项目页后再指定批次",
        }
        for item in products
    ]
