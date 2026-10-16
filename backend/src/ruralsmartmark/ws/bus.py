"""WebSocket 事件总线：所有连接收同一份事件流，不做角色裁剪（decisions #19）。

引擎在数据库 commit 成功之后才调用 broadcast（05 §4 铁律：先落库再广播）。
"""

import json

from fastapi import WebSocket


class EventBus:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def broadcast(self, type_: str, data: dict, sim_time: str) -> None:
        """向全体连接广播一条事件（JSON 序列化失败兜底 default=str）。"""
        message = json.dumps(
            {"type": type_, "sim_time": sim_time, "data": data},
            ensure_ascii=False,
            default=str,
        )
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                # 掉线客户端直接丢弃；发送失败不反噬广播方（主循环）
                self._clients.discard(ws)


bus = EventBus()
