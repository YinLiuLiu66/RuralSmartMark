"""虚拟时钟：1 tick = 1 模拟分钟。

模拟时间与真实时间分离（05 §4 铁律）：业务时间戳（trace/telemetry/运单时点）
一律取这里的一刻，绝不读墙钟。timestamptz 列要求带时区 aware datetime。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SIM_TZ = ZoneInfo("Asia/Shanghai")
# 剧本起点：演示日上午 7 点（世界从清晨开始转）
SIM_START = datetime(2026, 10, 16, 7, 0, tzinfo=SIM_TZ)
TICK_MINUTES = 1
# speed=1 时每 tick 的真实秒数；speed 为 1–10 倍率
BASE_TICK_SECONDS = 2.0


@dataclass
class SimClock:
    sim_time: datetime = SIM_START
    speed: float = 2.0
    running: bool = True
    tick_count: int = 0

    def advance(self) -> datetime:
        self.sim_time += timedelta(minutes=TICK_MINUTES)
        self.tick_count += 1
        return self.sim_time

    @property
    def tick_interval(self) -> float:
        return BASE_TICK_SECONDS / self.speed

    def snapshot(self) -> dict[str, object]:
        return {
            "sim_time": self.sim_time.isoformat(timespec="seconds"),
            "speed": self.speed,
            "running": self.running,
            "tick": self.tick_count,
        }
