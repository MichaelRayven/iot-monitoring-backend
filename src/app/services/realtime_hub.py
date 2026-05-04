import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, dev_eui: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._subscribers[dev_eui].add(websocket)

    async def unsubscribe(self, dev_eui: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._subscribers[dev_eui].discard(websocket)

    async def publish(self, dev_eui: str, message: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(dev_eui, set()))

        for ws in subscribers:
            try:
                await ws.send_json(message)
            except RuntimeError:
                await self.unsubscribe(dev_eui, ws)


hub = RealtimeHub()
