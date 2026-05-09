from app.schemas.device import DeviceResponse
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class FloorDeviceCreate(BaseModel):
    """Schema for adding a new floor device"""

    model_config = ConfigDict(from_attributes=True)

    dev_eui: str = Field(min_length=16, max_length=16)
    floor_id: int
    device_type: str | None = None
    is_stationary: bool = False
    x: float | None = None
    y: float | None = None


class FloorDeviceUpdate(BaseModel):
    """Schema for updating a floor device"""

    model_config = ConfigDict(from_attributes=True)

    floor_id: int | None = None
    device_type: str | None = None
    is_stationary: bool | None = None
    x: float | None = None
    y: float | None = None


class FloorDeviceResponse(DeviceResponse):
    """Schema for floor devices in responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    floor_id: int
    device_type: str | None = None
    is_stationary: bool = False
    x: float | None = None
    y: float | None = None


class FloorDeviceWithDataResponse(FloorDeviceResponse):
    """Schema for floor devices in responses with additional data field"""

    data: dict[str, Any] = Field(
        default_factory=dict(),
        description="Arbitrary data field, different for each device type",
    )
