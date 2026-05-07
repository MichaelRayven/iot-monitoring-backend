from typing import Any
from pydantic import BaseModel


class DeviceDataOutSchema(BaseModel):
    dev_eui: str
    name: str | None = None
    device_type: str | None = None
    rssi: int | None = None
    snr: float | None = None
    floor_id: int | None = None
    is_stationary: bool | None = None
    x: float | None = None
    y: float | None = None
    data: dict[str, Any] | None = None
