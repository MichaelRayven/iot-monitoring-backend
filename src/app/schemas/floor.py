from app.models.floor_devices import FloorDevice
from pydantic import BaseModel, Field, ConfigDict


class FloorCreate(BaseModel):
    """Schema for creating a new floor"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    building_id: int = Field(..., description="Parent building id")
    floorplan_key: str = Field(..., description="Floorplan image S3 key")
    scale_factor: int = Field(ge=1)


class FloorUpdate(BaseModel):
    """Schema for updating the floor (all fields optional)"""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Display name"
    )
    building_id: int | None = Field(None, description="Parent building id")
    floorplan_key: str | None = Field(None, description="Floorplan image S3 key")
    scale_factor: float | None = Field(default=None, ge=1)


class FloorResponse(BaseModel):
    """Schema for floor in responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class FloorFullResponse(FloorResponse):
    """Schema for full floor information in responses"""

    building_id: int
    floorplan_url: str
    scale_factor: int
    devices: list[FloorDevice] = []
