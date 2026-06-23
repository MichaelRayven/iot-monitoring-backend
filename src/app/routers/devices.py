import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    AsyncSessionDep,
    FloorServiceDep,
    PayloadDecoderServiceDep,
    VegaClientDep,
)
from app.models.floor_devices import FloorDevice, BEACON_DEVICE_TYPE
from app.schemas.device import DeviceResponse
from app.schemas.floor_device import (
    ConflictResponse,
    FloorDeviceCreate,
    FloorDeviceResponse,
    FloorDeviceUpdate,
    FloorDeviceWithDataResponse,
)
from app.schemas.pagination import PaginationParams
from app.schemas.vega.get_device_data import GetDeviceDataSelect
from app.services.payload_decoder_service import PayloadDecoderService
from app.services.vega_client import VegaClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["devices"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _enrich_with_vega(
    device: FloorDevice, vega_service: VegaClient
) -> FloorDeviceResponse:
    """Return a FloorDeviceResponse enriched with live Vega signal data."""
    vega_device = await vega_service.get_device_by_id(device.uid)
    return FloorDeviceResponse(
        id=device.id,
        floor_id=device.floor_id,
        uid=device.uid,
        name=vega_device.name if vega_device else None,
        device_type=device.device_type,
        is_stationary=device.is_stationary,
        x=device.x,
        y=device.y,
        rssi=vega_device.last_rssi if vega_device else None,
        snr=vega_device.last_snr if vega_device else None,
        last_data_ts=vega_device.last_data_ts if vega_device else None,
    )


def _beacon_response(device: FloorDevice) -> FloorDeviceResponse:
    """Build a FloorDeviceResponse for a beacon (no Vega enrichment)."""
    return FloorDeviceResponse(
        id=device.id,
        floor_id=device.floor_id,
        uid=device.uid,
        name=device.name,
        device_type=device.device_type,
        is_stationary=device.is_stationary,
        x=device.x,
        y=device.y,
    )


async def _get_nearby_badges(
    beacon_uid: str,
    db: AsyncSession,
    vega_service: VegaClient,
    payload_service: PayloadDecoderService,
) -> list[dict[str, Any]]:
    """
    Find Smart Badge devices that recently saw this beacon.

    Smart Badge uplinks embed the beacon MAC as raw 6-byte hex (e.g. "aabbccddeeff").
    Beacon uid is stored as colon-separated (e.g. "AA:BB:CC:DD:EE:FF").
    """
    mac_hex = beacon_uid.replace(":", "").lower()

    result = await db.execute(
        select(FloorDevice).where(FloorDevice.device_type == "Smart Badge")
    )
    badge_devices = list(result.scalars().all())

    nearby: list[dict[str, Any]] = []
    for badge in badge_devices:
        vega_data = await vega_service.get_device_data(
            badge.uid, GetDeviceDataSelect(limit=50)
        )
        for entry in vega_data.data_list:
            if not entry.data or not entry.port:
                continue
            decoded = payload_service.decode_payload("Smart Badge", entry)
            packet = decoded.get("packet")
            if packet not in ("nearest_ble_beacon", "three_nearest_ble_beacons"):
                continue
            for beacon_entry in decoded.get("beacons", []):
                entry_mac = beacon_entry.get("mac") or beacon_entry.get("mac_or_id", "")
                if entry_mac.lower() == mac_hex:
                    nearby.append(
                        {
                            "badge_uid": badge.uid,
                            "badge_name": badge.name,
                            "ts": decoded.get("device_timestamp"),
                            "rssi": beacon_entry.get("rssi"),
                            "battery_percent": decoded.get("battery_percent"),
                            "temperature_c": decoded.get("temperature_c"),
                        }
                    )
                    break

    return nearby


# ---------------------------------------------------------------------------
# Catalogue endpoints
# ---------------------------------------------------------------------------


@router.get("/types", response_model=list[str], summary="List supported device types")
async def get_device_types(decoder_service: PayloadDecoderServiceDep) -> list[str]:
    return decoder_service.get_supported_devices() + [BEACON_DEVICE_TYPE]


@router.get(
    "/vega",
    response_model=list[DeviceResponse],
    summary="List all devices registered on the Vega IoT server",
)
async def get_vega_devices(vega_service: VegaClientDep) -> list[DeviceResponse]:
    response = await vega_service.get_devices()
    if not response.status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device list from IoTVegaServer.",
        )
    return [
        DeviceResponse(
            dev_eui=device.dev_eui,
            name=device.name,
            rssi=device.last_rssi,
            snr=device.last_snr,
            last_data_ts=device.last_data_ts,
        )
        for device in response.devices_list
    ]


# ---------------------------------------------------------------------------
# Floor device list + creation
# ---------------------------------------------------------------------------


@router.get(
    "/floor/{floor_id}",
    response_model=list[FloorDeviceResponse],
    summary="List all devices assigned to a floor",
)
async def get_floor_devices(
    floor_id: int,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    pagination: PaginationParams = Depends(),
) -> list[FloorDeviceResponse]:
    try:
        devices = await service.get_floor_devices(
            floor_id=floor_id,
            skip=pagination.skip,
            limit=pagination.limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    results: list[FloorDeviceResponse] = []
    for device in devices:
        if device.is_beacon:
            results.append(_beacon_response(device))
        else:
            results.append(await _enrich_with_vega(device, vega_service))
    return results


@router.post(
    "/floor/{floor_id}",
    response_model=FloorDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a device (vega or beacon) to a floor",
    responses={409: {"model": ConflictResponse}},
)
async def add_device_to_floor(
    floor_id: int,
    device_data: FloorDeviceCreate,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
) -> FloorDeviceResponse:
    if device_data.device_type != BEACON_DEVICE_TYPE:
        vega_device = await vega_service.get_device_by_id(device_data.uid)
        if not vega_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vega device with uid {device_data.uid} not found on server",
            )

    existing = await service.get_device_by_uid(device_data.uid)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ConflictResponse(
                message=f"Device with uid {device_data.uid} already exists",
                existing_device_id=existing.id,
            ).model_dump(),
        )

    try:
        device = await service.add_device_to_floor(floor_id, device_data)

        if device.is_beacon:
            return _beacon_response(device)
        return await _enrich_with_vega(device, vega_service)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Single device — get with data, update, delete
# ---------------------------------------------------------------------------


@router.get(
    "/{device_id}",
    response_model=FloorDeviceWithDataResponse,
    summary="Get a device with its latest data",
)
async def get_floor_device(
    device_id: int,
    db: AsyncSessionDep,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    payload_service: PayloadDecoderServiceDep,
) -> FloorDeviceWithDataResponse:
    """
    Vega devices: returns decoded sensor history (last 50 packets).
    Beacons: returns nearby Smart Badge devices (matched via MAC address).
    """
    device = await service.get_floor_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found",
        )

    if device.is_beacon:
        nearby = await _get_nearby_badges(device.uid, db, vega_service, payload_service)
        return FloorDeviceWithDataResponse(
            id=device.id,
            floor_id=device.floor_id,
            uid=device.uid,
            name=device.name,
            device_type=device.device_type,
            x=device.x,
            y=device.y,
            nearby_badges=nearby,
        )

    vega_device = await vega_service.get_device_by_id(device.uid)
    vega_data = await vega_service.get_device_data(
        device.uid, GetDeviceDataSelect(limit=50)
    )

    decoded_data: list[dict[str, Any]] = []
    for entry in vega_data.data_list:
        if not entry.data or not entry.port:
            continue
        decoded_data.append(payload_service.decode_payload(device.device_type, entry))

    return FloorDeviceWithDataResponse(
        id=device.id,
        floor_id=device.floor_id,
        uid=device.uid,
        name=vega_device.name if vega_device else None,
        device_type=device.device_type,
        is_stationary=device.is_stationary,
        x=device.x,
        y=device.y,
        rssi=vega_device.last_rssi if vega_device else None,
        snr=vega_device.last_snr if vega_device else None,
        last_data_ts=vega_device.last_data_ts if vega_device else None,
        data=decoded_data,
    )


@router.put(
    "/{device_id}",
    response_model=FloorDeviceResponse,
    summary="Update a floor device",
)
async def update_floor_device(
    device_id: int,
    device_data: FloorDeviceUpdate,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
) -> FloorDeviceResponse:
    try:
        device = await service.update_floor_device(device_id, device_data)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found",
            )
        if device.is_beacon:
            return _beacon_response(device)
        return await _enrich_with_vega(device, vega_service)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a floor device",
)
async def delete_floor_device(device_id: int, service: FloorServiceDep) -> None:
    deleted = await service.delete_floor_device(device_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found",
        )
    return None
