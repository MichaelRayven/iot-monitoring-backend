from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

BEACON_DEVICE_TYPE = "Beacon"


# ---------------------------------------------------------------------------
# Create schema
# ---------------------------------------------------------------------------


class FloorDeviceCreate(BaseModel):
    """
    Payload for adding any floor device.

    - Beacon:      device_type="Beacon", uid=mac_address, name required
    - Vega device: device_type=<sensor type>, uid=dev_eui, name optional
                   (display name is fetched live from Vega)
    """

    model_config = ConfigDict(from_attributes=True)

    uid: str = Field(description="dev_eui (vega) or mac_address (beacon)")
    device_type: str = Field(description='"Beacon" or a Vega device type, e.g. "Smart-WB0101"')
    name: str | None = Field(
        default=None,
        description="Required for beacons. Vega devices use the name from Vega server.",
    )
    is_stationary: bool = False
    x: float | None = None
    y: float | None = None

    @model_validator(mode="after")
    def beacon_requires_name(self) -> FloorDeviceCreate:
        if self.device_type == BEACON_DEVICE_TYPE and not self.name:
            raise ValueError("name is required for Beacon devices")
        return self


# ---------------------------------------------------------------------------
# Update schema
# ---------------------------------------------------------------------------


class FloorDeviceUpdate(BaseModel):
    """Payload for updating any floor device. All fields optional."""

    model_config = ConfigDict(from_attributes=True)

    floor_id: int | None = None
    name: str | None = None
    device_type: str | None = None
    is_stationary: bool | None = None
    x: float | None = None
    y: float | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FloorDeviceResponse(BaseModel):
    """Unified response schema for any floor device."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    floor_id: int

    uid: str
    name: str | None = None
    device_type: str | None = None
    is_stationary: bool = False
    x: float | None = None
    y: float | None = None

    # Vega-only signal fields (null for beacons)
    rssi: int | None = None
    snr: float | None = None
    last_data_ts: int | None = None


class FloorDeviceWithDataResponse(FloorDeviceResponse):
    """Floor device response with sensor history or nearby badge data."""

    # Vega devices: decoded sensor payloads
    data: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Decoded sensor payloads (vega devices only)",
    )
    # Beacons: Smart Badge devices that recently saw this beacon
    nearby_badges: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Smart Badge devices that have recently seen this beacon",
    )


class ConflictResponse(BaseModel):
    """Structured 409 error body returned when a device UID already exists."""

    message: str
    existing_device_id: int
