"""ORM 模型汇总入口：alembic 与业务代码统一从这里 import。"""

from ruralsmartmark.models.auth import User
from ruralsmartmark.models.base import Base
from ruralsmartmark.models.business import (
    AgentArtifact,
    AgentTask,
    PriceBenchmark,
    ProductSku,
    Telemetry,
    TraceCode,
)
from ruralsmartmark.models.runtime import (
    Cooperative,
    Pallet,
    Shipment,
    Site,
    TraceEvent,
    Vehicle,
    Worker,
)

__all__ = [
    "Base",
    # 运行时实体（7）
    "Cooperative",
    "Site",
    "Vehicle",
    "Worker",
    "Pallet",
    "Shipment",
    "TraceEvent",
    # Agent/业务实体（6）
    "ProductSku",
    "Telemetry",
    "AgentTask",
    "AgentArtifact",
    "TraceCode",
    "PriceBenchmark",
    # 鉴权（M1-c 附加）
    "User",
]
