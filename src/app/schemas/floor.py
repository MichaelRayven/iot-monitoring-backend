from pydantic import BaseModel, Field


class FloorCreate(BaseModel):
    name: str
    building: str | None = None
    scale_factor: float = Field(gt=0)


class FloorUpdate(BaseModel):
    name: str | None = None
    building: str | None = None
    scale_factor: float | None = Field(default=None, gt=0)


class FloorDeviceCreate(BaseModel):
    dev_eui: str = Field(min_length=16, max_length=16)
    device_type: str | None = None
    is_stationary: bool = False
    x: float | None = None
    y: float | None = None


class FloorDevicePositionUpdate(BaseModel):
    x: float
    y: float


class FloorDeviceRead(BaseModel):
    id: int
    dev_eui: str
    device_type: str | None
    is_stationary: bool
    x: float | None
    y: float | None

    model_config = {"from_attributes": True}


class FloorRead(BaseModel):
    id: int
    name: str
    building: str | None
    floorplan_url: str | None
    scale_factor: float
    devices: list[FloorDeviceRead] = []

    model_config = {"from_attributes": True}
