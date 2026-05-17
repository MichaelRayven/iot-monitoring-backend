from typing import Any, Literal
from pydantic import BaseModel


class SubscribeMessage(BaseModel):
    action: Literal["subscribe"] = "subscribe"
    floor_id: str


class UnsubscribeMessage(BaseModel):
    action: Literal["unsubscribe"] = "unsubscribe"
    floor_id: str


class RealtimeUpdateMessage(BaseModel):
    action: Literal["update"] = "update"
    dev_eui: str
    floor_id: int
    device_type: str
    decoded: dict[str, Any]
