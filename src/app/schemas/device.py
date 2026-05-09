from pydantic import BaseModel, ConfigDict


class DeviceResponse(BaseModel):
    """Schema for devices in responses"""

    model_config = ConfigDict(from_attributes=True)

    dev_eui: str
    name: str | None = None
    rssi: int
    snr: float
    last_data_ts: int
