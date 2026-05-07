from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.connection_manager import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def subscribe_to_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
