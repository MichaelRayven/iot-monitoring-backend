from app.schemas.core import BaseVegaModel
from typing import Any, Literal

from pydantic import BaseModel, Field


class VegaRxPacket(BaseVegaModel):
    cmd: Literal["rx"] = "rx"
    devEui: str
    appEui: str | None = None
    gatewayId: str | None = None
    ack: bool | None = None
    fcnt: int | None = None
    port: int
    data: str
    freq: int | None = None
    dr: str | None = None
    rssi: int | None = None
    snr: float | None = None
    type: str | None = None


class DecodedPacket(BaseModel):
    dev_eui: str
    port: int
    raw_data: str
    device_type: str | None = None
    decoded: dict[str, Any]
    radio: dict[str, Any] = Field(default_factory=dict)
