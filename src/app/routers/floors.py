import logging
from app.models.floor_devices import FloorDevice
from app.schemas.vega.get_devices import GetDevicesSelect
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.core.deps import FloorServiceDep, S3StorageDep, VegaClientDep
from app.schemas.pagination import PaginationParams
from app.schemas.floor import FloorCreate, FloorUpdate, FloorResponse, FloorFullResponse
from app.schemas.floor_device import (
    FloorDeviceCreate,
    FloorDeviceUpdate,
    FloorDeviceResponse,
)

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
    summary="Get all floors for a specific building",
)
async def get_floors_by_building(
    building_id: int,
    service: FloorServiceDep,
    pagination: PaginationParams = Depends(),
    include_devices: bool = Query(False, description="Include devices in response"),
):
    floors = await service.get_floors_by_building(
        building_id=building_id,
        skip=pagination.skip,
        limit=pagination.limit,
        include_devices=include_devices,
    )

    return floors


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
                dev_eui_list=[device.dev_eui for device in floor.devices]  # ty:ignore[unknown-argument]
            )
        )
        devices_info: dict[str, FloorDevice] = {}
        for device in floor.devices:
            devices_info[device.dev_eui] = device

        for device in vega_devices.devices_list:
            info = devices_info.get(device.dev_eui)
            if not info:
                continue
            floor_devices.append(
                FloorDeviceResponse(
                    id=info.id,
                    dev_eui=device.dev_eui,
                    name=device.name,
                    rssi=device.last_rssi,
                    snr=device.last_snr,
                    last_data_ts=device.last_data_ts,
                    floor_id=info.floor_id,
                    is_stationary=info.is_stationary,
                    x=info.x,
                    y=info.y,
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


@router.get(
    "/{floor_id}/devices",
    response_model=list[FloorDeviceResponse],
    summary="Get all devices on a floor",
)
async def get_floor_devices(
    floor_id: int,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    pagination: PaginationParams = Depends(),
):
    try:
        devices = await service.get_floor_devices(
            floor_id=floor_id,
            skip=pagination.skip,
            limit=pagination.limit,
        )

        results: list[FloorDeviceResponse] = []
        for device in devices:
            vega_device = await vega_service.get_device_by_id(device.dev_eui)

            if not vega_device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Vega device with EUI {device.dev_eui} not found",
                )

            results.append(
                FloorDeviceResponse(
                    id=device.id,
                    dev_eui=device.dev_eui,
                    floor_id=device.floor_id,
                    name=vega_device.name,
                    device_type=device.device_type,
                    is_stationary=device.is_stationary,
                    x=device.x,
                    y=device.y,
                    rssi=vega_device.last_rssi,
                    snr=vega_device.last_snr,
                    last_data_ts=vega_device.last_data_ts,
                )
            )

        return results
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{floor_id}/devices",
    response_model=FloorDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a device to a floor",
)
async def add_device_to_floor(
    floor_id: int,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    device_data: FloorDeviceCreate,
):
    try:
        vega_device = await vega_service.get_device_by_id(device_data.dev_eui)

        if not vega_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vega device with EUI {device_data.dev_eui} not found",
            )

        device = await service.add_device_to_floor(floor_id, device_data)

        return FloorDeviceResponse(
            id=device.id,
            dev_eui=device.dev_eui,
            floor_id=device.floor_id,
            name=vega_device.name,
            device_type=device.device_type,
            is_stationary=device.is_stationary,
            x=device.x,
            y=device.y,
            rssi=vega_device.last_rssi,
            snr=vega_device.last_snr,
            last_data_ts=vega_device.last_data_ts,
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/devices/{device_id}",
    response_model=FloorDeviceResponse,
    summary="Get a specific device by ID",
)
async def get_floor_device(
    device_id: int, service: FloorServiceDep, vega_service: VegaClientDep
):
    """Get a specific device by its ID"""
    device = await service.get_floor_device(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found",
        )

    vega_device = await vega_service.get_device_by_id(device.dev_eui)

    if not vega_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vega device with EUI {device.dev_eui} not found",
        )

    return FloorDeviceResponse(
        id=device.id,
        dev_eui=device.dev_eui,
        floor_id=device.floor_id,
        name=vega_device.name,
        device_type=device.device_type,
        is_stationary=device.is_stationary,
        x=device.x,
        y=device.y,
        rssi=vega_device.last_rssi,
        snr=vega_device.last_snr,
        last_data_ts=vega_device.last_data_ts,
    )


@router.put(
    "/devices/{device_id}",
    response_model=FloorDeviceResponse,
    summary="Update a device",
)
async def update_floor_device(
    device_id: int,
    service: FloorServiceDep,
    vega_service: VegaClientDep,
    device_data: FloorDeviceUpdate,
):
    try:
        device = await service.update_floor_device(device_id, device_data)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found",
            )

        vega_device = await vega_service.get_device_by_id(device.dev_eui)

        if not vega_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vega device with EUI {device.dev_eui} not found",
            )

        return FloorDeviceResponse(
            id=device.id,
            dev_eui=device.dev_eui,
            floor_id=device.floor_id,
            name=vega_device.name,
            device_type=device.device_type,
            is_stationary=device.is_stationary,
            x=device.x,
            y=device.y,
            rssi=vega_device.last_rssi,
            snr=vega_device.last_snr,
            last_data_ts=vega_device.last_data_ts,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a device",
)
async def delete_floor_device(
    device_id: int,
    service: FloorServiceDep,
):
    deleted = await service.delete_floor_device(device_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found",
        )

    return None
