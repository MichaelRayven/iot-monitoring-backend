from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.services.connection_manager import manager
from app.schemas.subscribtions import SubscribeMessage, UnsubscribeMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def subscribe_to_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_json()

            action = message.get("action")

            if action == "subscribe":
                try:
                    sub_msg = SubscribeMessage.model_validate(message)
                    manager.subscribe(sub_msg.floor_id, websocket)
                    logger.debug(f"Client subscribed to floor {sub_msg.floor_id}")
                except ValidationError as e:
                    logger.warning(f"Invalid subscribe message: {e}")
            elif action == "unsubscribe":
                try:
                    unsub_msg = UnsubscribeMessage.model_validate(message)
                    manager.unsubscribe(unsub_msg.floor_id, websocket)
                    logger.debug(f"Client unsubscribed from floor {unsub_msg.floor_id}")
                except ValidationError as e:
                    logger.warning(f"Invalid unsubscribe message: {e}")
            else:
                logger.warning(f"Unknown action received: {action}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
