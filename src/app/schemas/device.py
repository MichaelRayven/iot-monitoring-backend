from pydantic import BaseModel, ConfigDict


class DeviceResponse(BaseModel):
    """Schema for Vega-registered devices in responses"""

    model_config = ConfigDict(from_attributes=True)

    dev_eui: str
    name: str | None = None
    rssi: int | None = None
    snr: float | None = None
    last_data_ts: int | None = None
