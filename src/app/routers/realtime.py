from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.realtime_hub import hub

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/devices/{dev_eui}")
async def subscribe_to_device(websocket: WebSocket, dev_eui: str):
    await websocket.accept()
    await hub.subscribe(dev_eui, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.unsubscribe(dev_eui, websocket)
