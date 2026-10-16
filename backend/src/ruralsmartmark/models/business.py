"""Agent / 业务实体表。"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ruralsmartmark.models.base import Base, TimestampMixin


class ProductSku(Base, TimestampMixin):
    __tablename__ = "product_sku"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # 指向品牌故事 artifact 的逻辑外键：不加 DB 层 FK——story 由 Agent 1 在
    # artifact 之后产出，DB 层约束会与 agent_artifact.task_id 形成循环依赖；
    # 需要时按 story_id 手工查询（M4 Agent 1 落地时再考虑加回 relationship）
    story_id: Mapped[int | None] = mapped_column(Integer)
    # 文创礼盒定价；散装行情只存 price_benchmark（溢价率单一算法，decisions #15）
    box_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class Telemetry(Base):
    """冷链温湿度流水（滚动窗口，按 vehicle_id + ts 查询）。

    不用 TimestampMixin：业务时间戳由模拟引擎写入，非数据库时钟。
    """

    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    temperature: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    humidity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)


class AgentTask(Base, TimestampMixin):
    __tablename__ = "agent_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # story（Agent 1）| design（Agent 2）| copy（Agent 3）
    # pricing（Agent 4）| dispatch（Agent 5）
    agent_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # pending | running | done | failed
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    product_sku_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_sku.id", ondelete="CASCADE")
    )
    created_by: Mapped[str] = mapped_column(String(60), nullable=False)

    artifacts: Mapped[list["AgentArtifact"]] = relationship(back_populates="task")


class AgentArtifact(Base, TimestampMixin):
    __tablename__ = "agent_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("agent_task.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # story | copy | design（Agent 2 图片资产存 asset_url）
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    # 图片资产挂静态目录：SiliconFlow URL 1 小时过期，
    # 本地转存后存相对路径（decisions #13）
    asset_url: Mapped[str | None] = mapped_column(String(255))
    # draft（AI 初稿）| polished（人工润色）| final（定稿）
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)

    task: Mapped[AgentTask] = relationship(back_populates="artifacts")

    __table_args__ = (
        UniqueConstraint("task_id", "kind", name="uq_artifact_task_kind"),
    )


class TraceCode(Base, TimestampMixin):
    __tablename__ = "trace_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 8 位 Base32 大写随机码（无歧义字符），消费者扫码入口 /t/:code
    code: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, index=True
    )
    # 唯一锚点：trace_code 只锚 pallet（decisions #15，shipment_id 已删除）
    pallet_id: Mapped[int] = mapped_column(
        ForeignKey("pallet.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PriceBenchmark(Base, TimestampMixin):
    __tablename__ = "price_benchmark"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku_id: Mapped[int] = mapped_column(
        ForeignKey("product_sku.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    # 散装行情价 vs 礼盒成交价；premium_rate = (brand - bulk) / bulk
    bulk_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    brand_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    premium_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
