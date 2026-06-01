from app.schemas.vega.get_device_data import GetDeviceDataSelect
import logging
from app.models.floor_devices import FloorDevice
from app.schemas.vega.get_devices import GetDevicesSelect
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.core.deps import (
    FloorServiceDep,
    S3StorageDep,
    VegaClientDep,
    PayloadDecoderServiceDep,
)
from app.schemas.pagination import PaginationParams
from app.schemas.floor import FloorCreate, FloorUpdate, FloorResponse, FloorFullResponse
from app.schemas.floor_device import FloorDeviceResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/floors", tags=["floors"])


@router.post(
    "/",
    response_model=FloorFullResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new floor",
)
async def create_floor(
    floor_data: FloorCreate,
    service: FloorServiceDep,
    s3_service: S3StorageDep,
):
    try:
        floor = await service.create_floor(floor_data)

        floorplan_url = s3_service.generate_download_url(floor.floorplan_key)

        return FloorFullResponse(
            id=floor.id,
            name=floor.name,
            building_id=floor.building_id,
            floorplan_url=floorplan_url,
            scale_factor=floor.scale_factor,
            devices=[],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntegrityError as _:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database integrity constraint violated",
        )


@router.get(
    "/building/{building_id}",
    response_model=list[FloorResponse],
    summary="List floors for a building",
)
async def get_floors_by_building(
    building_id: int,
    service: FloorServiceDep,
    pagination: PaginationParams = Depends(),
) -> list[FloorResponse]:
    floors = await service.get_floors_by_building(
        building_id=building_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [FloorResponse(id=f.id, name=f.name) for f in floors]


@router.get(
    "/{floor_id}",
    response_model=FloorFullResponse,
    summary="Get a specific floor by ID",
)
async def get_floor(
    floor_id: int,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    s3_service: S3StorageDep,
    include_devices: bool = Query(True, description="Include devices in response"),
):
    floor = await service.get_floor(floor_id, include_devices=include_devices)

    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Floor with ID {floor_id} not found",
        )

    floorplan_url = s3_service.generate_download_url(floor.floorplan_key)

    floor_devices: list[FloorDeviceResponse] = []

    if include_devices and floor.devices:
        vega_devices = await vega_service.get_devices(
            select=GetDevicesSelect(
                dev_eui_list=[device.uid for device in floor.devices if not device.is_beacon]  # ty:ignore[unknown-argument]
            )
        )
        devices_by_uid: dict[str, FloorDevice] = {d.uid: d for d in floor.devices}

        # Add Vega devices enriched with signal info
        for vega_dev in vega_devices.devices_list:
            info = devices_by_uid.get(vega_dev.dev_eui)
            if not info:
                continue
            floor_devices.append(
                FloorDeviceResponse(
                    id=info.id,
                    uid=vega_dev.dev_eui,
                    name=vega_dev.name,
                    rssi=vega_dev.last_rssi,
                    snr=vega_dev.last_snr,
                    last_data_ts=vega_dev.last_data_ts,
                    floor_id=info.floor_id,
                    device_type=info.device_type,
                    is_stationary=info.is_stationary,
                    x=info.x,
                    y=info.y,
                )
            )

        # Add beacons as-is (no Vega data)
        for device in floor.devices:
            if device.is_beacon:
                floor_devices.append(
                    FloorDeviceResponse(
                        id=device.id,
                        uid=device.uid,
                        name=device.name,
                        floor_id=device.floor_id,
                        device_type=device.device_type,
                        is_stationary=device.is_stationary,
                        x=device.x,
                        y=device.y,
                    )
                )

    return FloorFullResponse(
        id=floor.id,
        name=floor.name,
        building_id=floor.building_id,
        floorplan_url=floorplan_url,
        scale_factor=floor.scale_factor,
        devices=floor_devices,
    )


@router.put("/{floor_id}", response_model=FloorFullResponse, summary="Update a floor")
async def update_floor(
    floor_id: int,
    service: FloorServiceDep,
    s3_service: S3StorageDep,
    floor_data: FloorUpdate,
):
    try:
        floor = await service.update_floor(floor_id, floor_data)

        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Floor with ID {floor_id} not found",
            )

        floorplan_url = s3_service.generate_download_url(floor.floorplan_key)

        return FloorFullResponse(
            id=floor.id,
            name=floor.name,
            building_id=floor.building_id,
            floorplan_url=floorplan_url,
            scale_factor=floor.scale_factor,
            devices=[],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{floor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a floor"
)
async def delete_floor(
    floor_id: int,
    service: FloorServiceDep,
):
    deleted = await service.delete_floor(floor_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Floor with ID {floor_id} not found",
        )

    return None
