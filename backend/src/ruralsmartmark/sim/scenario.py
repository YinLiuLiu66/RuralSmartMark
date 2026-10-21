"""剧本（scenario）：初始世界生成 + 循环运转的叙事链路。

链路（站点坐标复用 M0 探针，M3 沙盘零漂移）：
  龙山镇蓝莓基地 --一程·时间驱动--> 县冷链集货仓 --二程·事件驱动--> 凯里前置仓
  --三程·越库直发--> 凯里门店

双写铁律（decisions #15，05 §4 铁律①）：每次状态转移 = 实体表现势回写
+ trace_event 追加一行（模拟时间存 payload.sim_ts，本表无时间列）。
跨 tick 只持主键/纯数据——每个 tick 独立 session，ORM 对象不跨 tick 持有。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.models import (
    Cooperative,
    Pallet,
    ProductSku,
    Shipment,
    Site,
    Telemetry,
    TraceCode,
    TraceEvent,
    Vehicle,
    Worker,
)
from ruralsmartmark.sim.clock import SimClock
from ruralsmartmark.sim.state_machines import shipment_next

# 站点与站 key 一一对应；坐标取 M0 探针 probeData.ts 同款
SITE_DEFS: tuple[tuple[str, str, float, float], ...] = (
    ("龙山镇蓝莓基地 · 产地", "origin_hub", -7.0, -1.5),
    ("麻江县冷链集货仓 · 分拣包装", "origin_hub", 0.0, 1.8),
    ("凯里前置仓", "forward_warehouse", 7.0, -1.2),
    ("凯里门店 · 礼盒专区", "market", 13.0, 1.2),
)
SITE_KEYS: tuple[str, ...] = ("farm", "hub", "depot", "market")

SKU_DEFS: tuple[tuple[str, float], ...] = (
    ("麻江蓝莓文创礼盒", 128.00),
    ("麻江蓝莓家庭装", 68.00),
)

# (vkey, 车牌, 常驻站)：truck1 只跑一程；truck2 跑二程 + 三程
VEHICLE_DEFS: tuple[tuple[str, str, str], ...] = (
    ("truck1", "冷链·麻江001", "farm"),
    ("truck2", "冷链·麻江002", "hub"),
)

WORKER_DEFS: tuple[tuple[str, str], ...] = (
    ("farm", "吴桂芳"),
    ("farm", "郑长河"),
    ("hub", "李淑芬"),
    ("depot", "赵建平"),
    ("market", "孙晓梅"),
)

CYCLE_TICKS = 100  # 一程周期（模拟分钟）
BATCH_PER_CYCLE = 4  # 每周期采摘托数
TRUCK2_THRESHOLD = 4  # 集货仓存货 ≥ 此值触发二程
MAX_CARGO = 8  # 单程装载上限

TEMP_BASE = 3.8
TEMP_JITTER = 0.6
HUMID_BASE = 42.0
TEMP_ALERT_AT = 8.0
# 每载货在途 tick 的越限概率：固定 seed 下确定，约一程触发一次（调参后复核）
ALERT_CHANCE_PER_TICK = 0.03

LEG1_JOURNEY = 26  # 农场→集货仓
LEG2_JOURNEY = 28  # 集货仓→前置仓
LEG3_JOURNEY = 24  # 前置仓→门店
RETURN1_TICKS = 16  # truck1 空驶返场
RETURN2_TICKS = 28  # truck2 空驶返仓


def _batch_no(cycle_no: int, j: int) -> str:
    return f"YL26-{cycle_no + 1:02d}{chr(65 + j)}"


def _num(v: Any) -> float | None:
    return float(v) if v is not None else None


def _iso(v: datetime | None) -> str | None:
    return v.isoformat(timespec="seconds") if v is not None else None


@dataclass
class WorldRefs:
    """初始世界的主键索引（纯数据，跨 tick 可持有）。"""

    site: dict[str, int] = field(default_factory=dict)
    vehicle: dict[str, int] = field(default_factory=dict)
    workers: dict[str, list[int]] = field(default_factory=dict)
    sku: dict[str, int] = field(default_factory=dict)


async def clear_world(session: AsyncSession) -> None:
    """清空运行时表（外键子表在前）。

    product_sku / user / agent_* 不动：参考与人工产出数据不随 reset 丢失。
    """
    for table in (
        TraceEvent,
        TraceCode,
        Telemetry,
        Shipment,
        Pallet,
        Vehicle,
        Worker,
        Site,
        Cooperative,
    ):
        await session.execute(delete(table))


async def build_initial_world(session: AsyncSession) -> WorldRefs:
    """重建初始世界：合作社 / 4 站点 / 2 车 / 5 工人 / SKU / 集货仓预置 4 托。"""
    refs = WorldRefs()

    for name, price in SKU_DEFS:
        sku = await session.scalar(select(ProductSku).where(ProductSku.name == name))
        if sku is None:
            sku = ProductSku(name=name, box_price=price)
            session.add(sku)
            await session.flush()
        refs.sku[name] = sku.id

    coop = Cooperative(
        name="麻江县蓝丰蓝莓合作社",
        contact="麻江县农业农村局对接",
        region="贵州省黔东南州麻江县",
    )
    session.add(coop)
    await session.flush()

    for key, (name, stype, x, z) in zip(SITE_KEYS, SITE_DEFS, strict=True):
        site = Site(
            cooperative_id=coop.id,
            name=name,
            type=stype,
            capacity=20,
            status="running",
            pos_x=x,
            pos_z=z,
        )
        session.add(site)
        await session.flush()
        refs.site[key] = site.id

    for site_key, worker_name in WORKER_DEFS:
        worker = Worker(site_id=refs.site[site_key], name=worker_name)
        session.add(worker)
        await session.flush()
        refs.workers.setdefault(site_key, []).append(worker.id)

    for vkey, plate, site_key in VEHICLE_DEFS:
        vehicle = Vehicle(
            plate=plate,
            status="docking",
            temperature=TEMP_BASE,
            humidity=HUMID_BASE,
            current_site_id=refs.site[site_key],
        )
        session.add(vehicle)
        await session.flush()
        refs.vehicle[vkey] = vehicle.id

    # 预置存货：世界开演 truck2 立即有货可拉，画面先动起来
    for j in range(TRUCK2_THRESHOLD):
        name, _ = SKU_DEFS[j % 2]
        session.add(
            Pallet(
                sku_id=refs.sku[name],
                qty=96 if j % 2 == 0 else 72,
                batch_no=_batch_no(0, j),
                current_site_id=refs.site["hub"],
            )
        )
    await session.flush()
    return refs


class WorldScript:
    """剧本运行时：主循环每 tick 调一次 step()。

    step() 返回待广播事件 [(type, data), ...]，由引擎在 commit 之后发送（铁律②）。
    """

    def __init__(self, clock: SimClock, rng: random.Random, refs: WorldRefs) -> None:
        self.clock = clock
        self.rng = rng
        self.refs = refs
        # 一程（时间驱动）：周期起点 / 批次托与运单
        self.cycle_start = clock.sim_time
        self.cycle_no = 0
        self.batch_pallet_ids: list[int] = []
        self.batch_shipment_id: int | None = None
        # 二程车（事件驱动）：trigger 后按 (offset, 动作) 队列推进
        self.t2_running = False
        self.t2_start = clock.sim_time
        self.t2_plan: list[tuple[int, Any]] = []
        self.t2_cargo_ids: list[int] = []
        self.t2_sid_a: int | None = None  # 二程运单（集货仓→前置仓）
        self.t2_sid_b: int | None = None  # 三程运单（前置仓→门店）
        # 在途路线（快照与客户端插值用）：vehicle_id → {from/to_site_id, 起止时间}
        self.routes: dict[int, dict[str, Any]] = {}
        self._events: list[tuple[str, dict[str, Any]]] = []

    async def step(self, session: AsyncSession) -> list[tuple[str, dict[str, Any]]]:
        self._events = []
        await self._tick_leg1(session)
        await self._tick_truck2(session)
        await self._tick_enroute(session)
        events = self._events
        self._events = []
        return events

    # ---- 一程（时间驱动）：t 命中周期内分钟数即触发对应动作 ----

    async def _tick_leg1(self, session: AsyncSession) -> None:
        t = self._cycle_offset()
        if t == 0:
            await self._harvest(session)
        elif t == 12:
            await self._trace_batch(
                session, "packed", site="farm", note="文创礼盒分装（12 盒/托）"
            )
        elif t == 22:
            await self._trace_batch(
                session, "stored", site="farm", note="产地冷库预冷暂存"
            )
            await self._set_workers(session, "farm", "idle")
        elif t == 26:
            await self._set_workers(session, "farm", "loading")
        elif t == 30:
            await self._confirm_leg1(session)
        elif t == 33:
            await self._ship_next(session, self.batch_shipment_id)
        elif t == 36:
            await self._load_batch(session)
        elif t == 42:
            await self._depart_leg1(session)
        elif t == 68:
            await self._arrive_leg1(session)
        elif t == 72:
            await self._set_vehicle(session, "truck1", "unloading", site="hub")
            await self._set_workers(session, "hub", "loading")
        elif t == 74:
            await self._drop_batch(session, "hub")
        elif t == 76:
            await self._ship_deliver(session, self.batch_shipment_id, idle="hub")
        elif t == 80:
            await self._set_vehicle(session, "truck1", "departed", site="hub")
        elif t == 82:
            await self._depart_empty(session, "truck1", "hub", "farm", RETURN1_TICKS)
        elif t == 98:
            await self._set_vehicle(session, "truck1", "docking", site="farm")
            self.routes.pop(self.refs.vehicle["truck1"], None)

    def _cycle_offset(self) -> int:
        t = int((self.clock.sim_time - self.cycle_start).total_seconds() // 60)
        if t >= CYCLE_TICKS:
            self.cycle_start += timedelta(minutes=CYCLE_TICKS)
            self.cycle_no += 1
            t -= CYCLE_TICKS
        return t

    async def _harvest(self, session: AsyncSession) -> None:
        self.batch_pallet_ids = []
        for j in range(BATCH_PER_CYCLE):
            name, _ = SKU_DEFS[j % 2]
            pallet = Pallet(
                sku_id=self.refs.sku[name],
                qty=96 if j % 2 == 0 else 72,
                batch_no=_batch_no(self.cycle_no, j),
                current_site_id=self.refs.site["farm"],
            )
            session.add(pallet)
            await session.flush()
            self.batch_pallet_ids.append(pallet.id)
            await self._trace_pallet(
                session,
                pallet,
                "harvested",
                site_id=self.refs.site["farm"],
                note="清晨采摘装托 · 龙山镇蓝莓基地 3 号田",
            )
        await self._set_workers(session, "farm", "sorting")

    async def _trace_batch(
        self,
        session: AsyncSession,
        kind: str,
        *,
        site: str | None = None,
        vehicle: str | None = None,
        note: str | None = None,
    ) -> None:
        site_id = self.refs.site[site] if site else None
        vehicle_id = self.refs.vehicle[vehicle] if vehicle else None
        for pid in self.batch_pallet_ids:
            pallet = await session.get(Pallet, pid)
            await self._trace_pallet(
                session,
                pallet,
                kind,
                site_id=site_id,
                vehicle_id=vehicle_id,
                note=note,
            )

    async def _confirm_leg1(self, session: AsyncSession) -> None:
        self.batch_shipment_id = await self._confirm(session, "farm", "hub", "truck1")

    async def _load_batch(self, session: AsyncSession) -> None:
        vid = self.refs.vehicle["truck1"]
        for pid in self.batch_pallet_ids:
            pallet = await session.get(Pallet, pid)
            pallet.current_site_id = None
            pallet.current_vehicle_id = vid
            await session.flush()
            await self._trace_pallet(
                session, pallet, "loaded", vehicle_id=vid, note="冷链车装载出库"
            )

    async def _depart_leg1(self, session: AsyncSession) -> None:
        vid = self.refs.vehicle["truck1"]
        self.routes[vid] = self._route("farm", "hub", LEG1_JOURNEY)
        await self._trace_batch(
            session, "departed", vehicle="truck1", note="冷链车发车，运单进入在途"
        )
        await self._ship_next(session, self.batch_shipment_id, departed=True)
        await self._set_vehicle(session, "truck1", "en_route", clear=True)
        await self._set_workers(session, "farm", "idle")

    async def _arrive_leg1(self, session: AsyncSession) -> None:
        self.routes.pop(self.refs.vehicle["truck1"], None)
        await self._set_vehicle(session, "truck1", "docking", site="hub")
        await self._trace_batch(session, "arrived", site="hub", note="到站，等待卸货")

    async def _drop_batch(self, session: AsyncSession, site_key: str) -> None:
        site_id = self.refs.site[site_key]
        for pid in self.batch_pallet_ids:
            pallet = await session.get(Pallet, pid)
            pallet.current_vehicle_id = None
            pallet.current_site_id = site_id
            await session.flush()
            await self._trace_pallet(
                session, pallet, "unloaded", site_id=site_id, note="卸货入仓"
            )

    # ---- 二程/三程（事件驱动）：集货仓存量 ≥ 阈值 → 走整段计划 ----

    async def _tick_truck2(self, session: AsyncSession) -> None:
        if not self.t2_running:
            await self._maybe_start_truck2(session)
            return
        elapsed = self._since(self.t2_start)
        while self.t2_plan and self.t2_plan[0][0] <= elapsed:
            _, action = self.t2_plan.pop(0)
            await action(session)

    async def _maybe_start_truck2(self, session: AsyncSession) -> None:
        truck2 = await session.get(Vehicle, self.refs.vehicle["truck2"])
        if (
            truck2.status != "docking"
            or truck2.current_site_id != self.refs.site["hub"]
        ):
            return
        stock = await session.scalar(
            select(func.count())
            .select_from(Pallet)
            .where(Pallet.current_site_id == self.refs.site["hub"])
        )
        if (stock or 0) < TRUCK2_THRESHOLD:
            return
        self.t2_running = True
        self.t2_start = self.clock.sim_time
        self.t2_cargo_ids = []
        self.t2_sid_a = await self._confirm(session, "hub", "depot", "truck2")
        self.t2_sid_b = None
        self.t2_plan = [
            # 注意：action 只允许 (session) 一个入参，partial 一律传关键字
            (0, partial(self._ship_next, sid=self.t2_sid_a)),
            (3, partial(self._ship_next, sid=self.t2_sid_a)),
            (6, partial(self._load_cargo, site_key="hub")),
            (10, partial(self._depart_leg2, sid=self.t2_sid_a)),
            (38, partial(self._arrive_truck2, site_key="depot")),
            (42, partial(self._set_vehicle, vkey="truck2", status="unloading")),
            (44, partial(self._unload_cargo, site_key="depot")),
            (46, partial(self._deliver_a_confirm_b, sid_a=self.t2_sid_a)),
            (49, self._ship_next_b),
            (52, partial(self._load_cargo, site_key="depot")),
            (55, self._depart_leg3),
            (79, partial(self._arrive_truck2, site_key="market")),
            (83, partial(self._set_vehicle, vkey="truck2", status="unloading")),
            (85, partial(self._unload_cargo, site_key="market")),
            (87, self._deliver_b),
            (90, partial(self._set_vehicle, vkey="truck2", status="departed")),
            (
                91,
                partial(
                    self._depart_empty,
                    vkey="truck2",
                    src="market",
                    dst="hub",
                    minutes=RETURN2_TICKS,
                ),
            ),
            (119, self._finish_truck2),
        ]

    async def _ship_next_b(self, session: AsyncSession) -> None:
        # 三程运单在计划构建时还不存在，触发时才读 id
        await self._ship_next(session, self.t2_sid_b)

    async def _deliver_b(self, session: AsyncSession) -> None:
        await self._ship_deliver(session, self.t2_sid_b, idle="market")

    async def _confirm(
        self, session: AsyncSession, src: str, dst: str, vkey: str
    ) -> int:
        shipment = Shipment(
            from_site_id=self.refs.site[src],
            to_site_id=self.refs.site[dst],
            vehicle_id=self.refs.vehicle[vkey],
            status="confirmed",
        )
        session.add(shipment)
        await session.flush()
        self._emit_shipment(shipment)
        return shipment.id

    async def _load_cargo(self, session: AsyncSession, site_key: str) -> None:
        vid = self.refs.vehicle["truck2"]
        cargo = (
            (
                await session.execute(
                    select(Pallet)
                    .where(Pallet.current_site_id == self.refs.site[site_key])
                    .order_by(Pallet.id)
                    .limit(MAX_CARGO)
                )
            )
            .scalars()
            .all()
        )
        self.t2_cargo_ids = [p.id for p in cargo]
        for pallet in cargo:
            pallet.current_site_id = None
            pallet.current_vehicle_id = vid
            await session.flush()
            await self._trace_pallet(
                session, pallet, "loaded", vehicle_id=vid, note="冷链车装载出库"
            )
        if cargo:
            await self._set_workers(session, site_key, "loading")

    async def _depart_leg2(self, session: AsyncSession, sid: int) -> None:
        self.routes[self.refs.vehicle["truck2"]] = self._route(
            "hub", "depot", LEG2_JOURNEY
        )
        await self._depart_common(session, sid, "hub")

    async def _depart_leg3(self, session: AsyncSession) -> None:
        self.routes[self.refs.vehicle["truck2"]] = self._route(
            "depot", "market", LEG3_JOURNEY
        )
        await self._depart_common(session, self.t2_sid_b, "depot")

    async def _depart_common(
        self, session: AsyncSession, sid: int | None, idle_site: str
    ) -> None:
        vid = self.refs.vehicle["truck2"]
        for pid in self.t2_cargo_ids:
            pallet = await session.get(Pallet, pid)
            await self._trace_pallet(
                session,
                pallet,
                "departed",
                vehicle_id=vid,
                note="冷链车发车，运单进入在途",
            )
        await self._ship_next(session, sid, departed=True)
        await self._set_vehicle(session, "truck2", "en_route", clear=True)
        await self._set_workers(session, idle_site, "idle")

    async def _arrive_truck2(self, session: AsyncSession, site_key: str) -> None:
        self.routes.pop(self.refs.vehicle["truck2"], None)
        await self._set_vehicle(session, "truck2", "docking", site=site_key)
        for pid in self.t2_cargo_ids:
            pallet = await session.get(Pallet, pid)
            await self._trace_pallet(
                session,
                pallet,
                "arrived",
                site_id=self.refs.site[site_key],
                note="到站，等待卸货",
            )

    async def _unload_cargo(self, session: AsyncSession, site_key: str) -> None:
        site_id = self.refs.site[site_key]
        for pid in self.t2_cargo_ids:
            pallet = await session.get(Pallet, pid)
            pallet.current_vehicle_id = None
            pallet.current_site_id = site_id
            await session.flush()
            await self._trace_pallet(
                session, pallet, "unloaded", site_id=site_id, note="卸货入仓"
            )
        await self._set_workers(session, site_key, "loading")

    async def _deliver_a_confirm_b(self, session: AsyncSession, sid_a: int) -> None:
        await self._ship_deliver(session, sid_a)
        self.t2_sid_b = await self._confirm(session, "depot", "market", "truck2")

    async def _finish_truck2(self, session: AsyncSession) -> None:
        await self._set_vehicle(session, "truck2", "docking", site="hub")
        self.t2_running = False
        self.t2_plan = []
        self.t2_cargo_ids = []

    # ---- 在途数据流：en_route 车辆每 tick 写 telemetry；载货偶发越限告警 ----

    async def _tick_enroute(self, session: AsyncSession) -> None:
        vehicles = (
            (await session.execute(select(Vehicle).where(Vehicle.status == "en_route")))
            .scalars()
            .all()
        )
        for vehicle in vehicles:
            temp = TEMP_BASE + self.rng.gauss(0, TEMP_JITTER)
            humid = HUMID_BASE + self.rng.gauss(0, 3.0)
            cargo_ids = (
                (
                    await session.execute(
                        select(Pallet.id).where(Pallet.current_vehicle_id == vehicle.id)
                    )
                )
                .scalars()
                .all()
            )
            alert = bool(cargo_ids) and self.rng.random() < ALERT_CHANCE_PER_TICK
            if alert:
                temp = TEMP_ALERT_AT + abs(self.rng.gauss(0, 0.4))
            vehicle.temperature = round(temp, 2)
            vehicle.humidity = round(humid, 2)
            session.add(
                Telemetry(
                    vehicle_id=vehicle.id,
                    ts=self.clock.sim_time,
                    temperature=vehicle.temperature,
                    humidity=vehicle.humidity,
                )
            )
            if alert:
                for pid in cargo_ids:
                    pallet = await session.get(Pallet, pid)
                    await self._trace_pallet(
                        session,
                        pallet,
                        "temp_alert",
                        vehicle_id=vehicle.id,
                        note="冷链温度越限告警",
                        temperature=round(temp, 2),
                    )
            self._emit_vehicle(vehicle)

    # ---- 运单推步 / 车辆与工人回写 ----

    async def _ship_next(
        self,
        session: AsyncSession,
        sid: int | None = None,
        *,
        departed: bool = False,
    ) -> None:
        shipment = await session.get(Shipment, sid) if sid else None
        if shipment is None:
            return
        nxt = shipment_next(shipment.status)
        if nxt is None:
            return
        shipment.status = nxt
        if nxt == "in_transit" and departed:
            shipment.departed_at = self.clock.sim_time
        self._emit_shipment(shipment)

    async def _ship_deliver(
        self,
        session: AsyncSession,
        sid: int | None = None,
        *,
        idle: str | None = None,
    ) -> None:
        shipment = await session.get(Shipment, sid) if sid else None
        if shipment is None:
            return
        shipment.status = "delivered"
        shipment.delivered_at = self.clock.sim_time
        self._emit_shipment(shipment)
        if idle:
            await self._set_workers(session, idle, "idle")

    async def _depart_empty(
        self, session: AsyncSession, vkey: str, src: str, dst: str, minutes: int
    ) -> None:
        """空驶返程：不计运单、不落 trace，只有车辆位置与路线变化。"""
        vid = self.refs.vehicle[vkey]
        self.routes[vid] = self._route(src, dst, minutes)
        await self._set_vehicle(session, vkey, "en_route", clear=True)

    async def _set_vehicle(
        self,
        session: AsyncSession,
        vkey: str,
        status: str,
        *,
        site: str | None = None,
        clear: bool = False,
    ) -> Vehicle:
        vehicle = await session.get(Vehicle, self.refs.vehicle[vkey])
        vehicle.status = status
        if site is not None:
            vehicle.current_site_id = self.refs.site[site]
        elif clear:
            vehicle.current_site_id = None
        self._emit_vehicle(vehicle)
        return vehicle

    async def _set_workers(
        self, session: AsyncSession, site_key: str, status: str
    ) -> None:
        for wid in self.refs.workers.get(site_key, []):
            worker = await session.get(Worker, wid)
            worker.status = status
            self._events.append(
                (
                    "entity.updated",
                    {
                        "entity": "worker",
                        "id": worker.id,
                        "site_id": worker.site_id,
                        "name": worker.name,
                        "status": worker.status,
                        "moves_today": worker.moves_today,
                    },
                )
            )

    async def _trace_pallet(
        self,
        session: AsyncSession,
        pallet: Pallet,
        kind: str,
        *,
        site_id: int | None = None,
        vehicle_id: int | None = None,
        note: str | None = None,
        **payload_extra: Any,
    ) -> None:
        """双写：trace_event 追加一行（模拟时间进 payload.sim_ts）+ 沙盘实体事件。"""
        payload: dict[str, Any] = {"sim_ts": self._sim_ts(), **payload_extra}
        session.add(
            TraceEvent(
                pallet_id=pallet.id,
                site_id=site_id,
                vehicle_id=vehicle_id,
                kind=kind,
                payload=payload,
                note=note,
            )
        )
        self._emit_pallet(pallet)

    # ---- 事件拼装帮手 ----

    def _sim_ts(self) -> str:
        return self.clock.sim_time.isoformat(timespec="seconds")

    def _since(self, since: datetime) -> int:
        return int((self.clock.sim_time - since).total_seconds() // 60)

    def _route(self, src: str, dst: str, minutes: int) -> dict[str, Any]:
        departed = self.clock.sim_time
        return {
            "from_site_id": self.refs.site[src],
            "to_site_id": self.refs.site[dst],
            "departed_at": departed.isoformat(timespec="seconds"),
            "arrives_at": (departed + timedelta(minutes=minutes)).isoformat(
                timespec="seconds"
            ),
        }

    def _emit_pallet(self, pallet: Pallet) -> None:
        self._events.append(
            (
                "entity.updated",
                {
                    "entity": "pallet",
                    "id": pallet.id,
                    "sku_id": pallet.sku_id,
                    "qty": pallet.qty,
                    "batch_no": pallet.batch_no,
                    "current_site_id": pallet.current_site_id,
                    "current_vehicle_id": pallet.current_vehicle_id,
                },
            )
        )

    def _emit_vehicle(self, vehicle: Vehicle) -> None:
        self._events.append(
            (
                "entity.updated",
                {
                    "entity": "vehicle",
                    "id": vehicle.id,
                    "plate": vehicle.plate,
                    "status": vehicle.status,
                    "temperature": _num(vehicle.temperature),
                    "humidity": _num(vehicle.humidity),
                    "current_site_id": vehicle.current_site_id,
                    "route": self.routes.get(vehicle.id),
                },
            )
        )

    def _emit_shipment(self, shipment: Shipment) -> None:
        self._events.append(
            (
                "shipment.progressed",
                {
                    "id": shipment.id,
                    "from_site_id": shipment.from_site_id,
                    "to_site_id": shipment.to_site_id,
                    "vehicle_id": shipment.vehicle_id,
                    "status": shipment.status,
                    "departed_at": _iso(shipment.departed_at),
                    "delivered_at": _iso(shipment.delivered_at),
                },
            )
        )


async def create_world(
    session: AsyncSession, clock: SimClock, rng: random.Random
) -> WorldScript:
    """清空运行时数据并重建剧本起点（引擎 reset 与首次 ensure 的唯一入口）。"""
    await clear_world(session)
    refs = await build_initial_world(session)
    return WorldScript(clock, rng, refs)
