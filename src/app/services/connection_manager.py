from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}
        self.active_subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        subscribtions = self.active_connections.pop(websocket)
        for sub in subscribtions:
            self.unsubscribe(sub, websocket)

    def subscribe(self, floor_id: str, websocket: WebSocket):
        self.active_subscriptions[floor_id].add(websocket)

    def unsubscribe(self, floor_id: str, websocket: WebSocket):
        self.active_subscriptions[floor_id].remove(websocket)

    async def send_update(self, floor_id: str, message: str):
        connections = self.active_subscriptions[floor_id]
        for connection in connections:
            await connection.send_text(message)


manager = ConnectionManager()
