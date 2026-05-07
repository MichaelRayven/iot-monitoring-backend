from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BuildingResponse(BaseModel):
    """Schema for building in responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(..., min_length=1, max_length=255, description="Building name")
    address: str = Field(
        ..., min_length=1, max_length=255, description="Building address"
    )


class BuildingCreate(BaseModel):
    """Schema for creating a new building"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Building name")
    address: str = Field(
        ..., min_length=1, max_length=255, description="Building address"
    )


class BuildingUpdate(BaseModel):
    """Schema for updating a building (all fields optional)"""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
