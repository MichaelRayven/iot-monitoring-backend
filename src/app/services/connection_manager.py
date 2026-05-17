from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}
        self.active_subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            subscriptions = self.active_connections.pop(websocket)
            for sub in list(subscriptions):
                self.unsubscribe(sub, websocket)

    def subscribe(self, floor_id: str, websocket: WebSocket):
        if floor_id not in self.active_subscriptions:
            self.active_subscriptions[floor_id] = set()
        self.active_subscriptions[floor_id].add(websocket)
        if websocket in self.active_connections:
            self.active_connections[websocket].add(floor_id)

    def unsubscribe(self, floor_id: str, websocket: WebSocket):
        if floor_id in self.active_subscriptions:
            self.active_subscriptions[floor_id].discard(websocket)
            if not self.active_subscriptions[floor_id]:
                del self.active_subscriptions[floor_id]
        if websocket in self.active_connections:
            self.active_connections[websocket].discard(floor_id)

    async def send_update(self, floor_id: str, message: str):
        connections = self.active_subscriptions.get(floor_id, set())
        for connection in list(connections):
            await connection.send_text(message)


manager = ConnectionManager()
