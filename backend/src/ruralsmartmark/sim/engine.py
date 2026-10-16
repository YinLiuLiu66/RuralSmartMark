"""SimEngine：虚拟时钟驱动剧本推进 → 落库 → WS 广播（decisions #5/#15/#17）。

生命周期归 FastAPI lifespan：start() 重建剧本世界并拉起主循环（重启 = 演示起点），
stop() 取消任务。控制动作（pause/resume/speed）在单线程 asyncio 下即时生效并
立即广播 tick.info（#17：时钟状态变化经既有 tick.info 事件广播）。
reset 用同倍速新时钟重建世界——演示任意时刻可回到剧本起点无限重放（#5）。
"""

import asyncio
import contextlib
import logging
import random

from ruralsmartmark import db
from ruralsmartmark.config import settings
from ruralsmartmark.sim.clock import SimClock
from ruralsmartmark.sim.scenario import WorldScript, create_world
from ruralsmartmark.ws.bus import bus

logger = logging.getLogger(__name__)


class SimEngine:
    def __init__(self) -> None:
        self.clock = SimClock()
        self.rng = random.Random(settings.sim_seed)
        self.script: WorldScript | None = None
        self._task: asyncio.Task[None] | None = None

    # ---- 生命周期 ----

    async def start(self) -> None:
        """FastAPI lifespan 入口：重置到剧本起点 + 拉起 tick 主循环。"""
        await self.reset()
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None

    async def reset(self) -> None:
        seed = settings.sim_seed
        self.rng = random.Random(seed)
        clock = SimClock(speed=self.clock.speed)  # reset 保留当前倍速
        async with db.session_factory() as session, session.begin():
            script = await create_world(session, clock, self.rng)
        self.clock = clock
        self.script = script
        await bus.broadcast(
            "world.reset", {"clock": clock.snapshot()}, self._iso(clock)
        )

    # ---- 控制（REST 入口见 routes/sim.py）----

    async def control(
        self, action: str, speed: float | None = None
    ) -> dict[str, object]:
        if action == "pause":
            self.clock.running = False
        elif action == "resume":
            self.clock.running = True
        elif action == "speed":
            self.clock.speed = float(speed or 1)
        elif action == "reset":
            await self.reset()
            return self.clock.snapshot()
        else:  # pragma: no cover — 路由层 Literal 已限定取值
            raise ValueError(action)
        await bus.broadcast("tick.info", self.clock.snapshot(), self._iso_now())
        return self.clock.snapshot()

    # ---- 主循环 ----

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.clock.tick_interval)
            if not self.clock.running:
                continue
            try:
                await self._tick()
            except Exception:
                # 主循环不许死：单 tick 失败（如 reset 竞态下的 FK 抖动）记日志继续
                logger.exception("sim tick failed")

    async def _tick(self) -> None:
        script = self.script
        if script is None:
            return
        # 先落库（铁律②：commit 成功后才广播），再推时钟
        async with db.session_factory() as session, session.begin():
            events = await script.step(session)
        sim_time = self._iso_now()
        await bus.broadcast("tick.info", self.clock.snapshot(), sim_time)
        for etype, data in events:
            await bus.broadcast(etype, data, sim_time)
        self.clock.advance()

    # ---- 供快照路由读取的内存态 ----

    def clock_snapshot(self) -> dict[str, object]:
        return self.clock.snapshot()

    def routes_snapshot(self) -> dict[int, dict[str, object]]:
        """在途路线（vehicle_id → 起止站与起止时间），供客户端插值。"""
        return dict(self.script.routes) if self.script else {}

    def _iso_now(self) -> str:
        return self.clock.sim_time.isoformat(timespec="seconds")

    @staticmethod
    def _iso(clock: SimClock) -> str:
        return clock.sim_time.isoformat(timespec="seconds")


engine = SimEngine()
