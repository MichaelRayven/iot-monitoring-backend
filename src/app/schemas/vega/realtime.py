from pydantic import Field
from typing import Literal
from app.schemas.vega.base import BaseVegaModel


class RxPacket(BaseVegaModel):
    cmd: Literal["rx"] = "rx"

    app_eui: str = Field(..., alias="appEui")
    dev_eui: str = Field(..., alias="devEui")
    gateway_id: str = Field(..., alias="gatewayId")
    port: int
    data: str
    mac_data: str | None = Field(default=None, alias="macData")
    ack: bool
    fcnt: int
    rssi: int
    snr: float
    ts: int
    type: str
