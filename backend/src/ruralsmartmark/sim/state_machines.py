"""实体状态机：合法枚举与流转助手（03 数据模型 §2 五步运单）。"""

# 运单五步：订单确认 → 提货 → 装车 → 在途 → 送达（单向前进一步）
SHIPMENT_NEXT: dict[str, str] = {
    "confirmed": "picked",
    "picked": "loaded",
    "loaded": "in_transit",
    "in_transit": "delivered",
}

# 车辆状态全集（runtime.Vehicle 注释同源）：靠站 | 在途 | 卸货中 | 返程离站
VEHICLE_STATUSES = frozenset({"docking", "en_route", "unloading", "departed"})

# worker 状态全集：空闲 | 分拣 | 装卸 | 下班
WORKER_STATUSES = frozenset({"idle", "sorting", "loading", "off_duty"})


def shipment_next(status: str) -> str | None:
    """运单沿五步状态机走一步；已送达返回 None。"""
    return SHIPMENT_NEXT.get(status)
