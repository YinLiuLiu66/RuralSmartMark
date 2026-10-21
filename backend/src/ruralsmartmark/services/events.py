import asyncio
import itertools
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._seq = itertools.count(1)

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        event = {"id": next(self._seq), "type": event_type, "data": data}
        for queue in list(self._subscribers):
            queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)


bus = EventBus()
