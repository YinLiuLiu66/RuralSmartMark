"""运行时实体表（模拟引擎持续更新）。

现势状态存实体表（沙盘/REST 读），历史过程存事件表 trace_event（溯源页读）
——decisions #15确立的全库模式。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ruralsmartmark.models.base import Base, TimestampMixin


class Cooperative(Base, TimestampMixin):
    __tablename__ = "cooperative"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    contact: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))

    sites: Mapped[list["Site"]] = relationship(back_populates="cooperative")


class Site(Base, TimestampMixin):
    __tablename__ = "site"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cooperative_id: Mapped[int | None] = mapped_column(
        ForeignKey("cooperative.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # origin_hub（产地集货仓）| forward_warehouse（城市前置仓）| market（消费端门店）
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # running | idle | full
    status: Mapped[str] = mapped_column(String(16), default="running", nullable=False)
    # 沙盘摆位（探针同款坐标体系）
    pos_x: Mapped[float] = mapped_column(Numeric(8, 2), default=0, nullable=False)
    pos_z: Mapped[float] = mapped_column(Numeric(8, 2), default=0, nullable=False)

    cooperative: Mapped[Cooperative | None] = relationship(back_populates="sites")
    pallets: Mapped[list["Pallet"]] = relationship(back_populates="site")


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plate: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    # en_route | docking | unloading | departed（03 文档五步状态机配套）
    status: Mapped[str] = mapped_column(String(16), default="docking", nullable=False)
    temperature: Mapped[float | None] = mapped_column(Numeric(5, 2))
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # 现势：车辆当前所在站点（空 = 在途）
    current_site_id: Mapped[int | None] = mapped_column(
        ForeignKey("site.id", ondelete="SET NULL")
    )


class Worker(Base, TimestampMixin):
    __tablename__ = "worker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(
        ForeignKey("site.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    # idle | sorting | loading | off_duty
    status: Mapped[str] = mapped_column(String(16), default="idle", nullable=False)
    moves_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Pallet(Base, TimestampMixin):
    __tablename__ = "pallet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_sku.id", ondelete="SET NULL")
    )
    qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    batch_no: Mapped[str] = mapped_column(String(40), nullable=False)
    # 现势字段（decisions #15）：托盘当前在站点或在车上，二者至多一个非空
    current_site_id: Mapped[int | None] = mapped_column(
        ForeignKey("site.id", ondelete="SET NULL")
    )
    current_vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle.id", ondelete="SET NULL")
    )

    __table_args__ = (
        CheckConstraint(
            "(current_site_id IS NULL) <> (current_vehicle_id IS NULL)",
            name="ck_pallet_location_xor",
        ),
    )

    site: Mapped[Site | None] = relationship(back_populates="pallets")
    trace_events: Mapped[list["TraceEvent"]] = relationship(back_populates="pallet")


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_site_id: Mapped[int] = mapped_column(
        ForeignKey("site.id", ondelete="RESTRICT"), nullable=False
    )
    to_site_id: Mapped[int] = mapped_column(
        ForeignKey("site.id", ondelete="RESTRICT"), nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicle.id", ondelete="RESTRICT"), nullable=False
    )
    # confirmed | picked | loaded | in_transit | delivered（五步状态机）
    status: Mapped[str] = mapped_column(String(16), default="confirmed", nullable=False)
    departed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TraceEvent(Base):
    """溯源事件流水，append-only：只写不改（decisions #15）。

    模拟引擎在每个关键节点写入一行；溯源页时间线按 pallet_id 查本表。
    """

    __tablename__ = "trace_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pallet_id: Mapped[int] = mapped_column(
        ForeignKey("pallet.id", ondelete="CASCADE"), nullable=False, index=True
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("site.id", ondelete="SET NULL")
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle.id", ondelete="SET NULL")
    )
    # harvested | packed | stored | loaded | departed | arrived
    # unloaded | delivered | temp_alert
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    pallet: Mapped[Pallet] = relationship(back_populates="trace_events")
