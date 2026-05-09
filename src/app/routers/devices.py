from app.schemas.devices import DeviceDataOutSchema
from app.core.deps import AsyncSessionDep, VegaClientDep
from app.models.floor_devices import FloorDevice
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.services.payload_decoders import decode_payload

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceDataOutSchema])
async def get_devices(service: VegaClientDep, db: AsyncSessionDep):
    response = await service.get_devices()

    if not response.status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device list from IoTVegaServer.",
        )

    dev_euis = [device.dev_eui for device in response.devices_list]

    floor_devices_by_eui: dict[str, FloorDevice] = {}
    if dev_euis:
        result = await db.execute(
            select(FloorDevice).where(FloorDevice.dev_eui.in_(dev_euis))
        )
        for floor_device in result.scalars():
            floor_devices_by_eui.setdefault(floor_device.dev_eui, floor_device)

    result: list[DeviceDataOutSchema] = []
    for device in response.devices_list:
        floor_device = floor_devices_by_eui.get(device.dev_eui)
        device_type = floor_device.device_type if floor_device is not None else None
        result.append(
            DeviceDataOutSchema(
                dev_eui=device.dev_eui,
                name=device.dev_name,
                device_type=device_type,
                rssi=device.last_rssi,
                snr=device.last_snr,
                floor_id=floor_device.floor_id if floor_device is not None else None,
                is_stationary=floor_device.is_stationary
                if floor_device is not None
                else None,
                x=floor_device.x if floor_device is not None else None,
                y=floor_device.y if floor_device is not None else None,
                data=None,
            )
        )

    return result


@router.post("/{dev_eui}/data")
async def get_device_data(
    service: VegaClientDep,
    dev_eui: str,
    device_type: str | None = None,
):
    response = await service.get_device_data(dev_eui=dev_eui)

    data_list = response.data_list
    decoded = []

    for item in data_list:
        raw_data = item.data
        port = item.port

        decoded.append(
            {
                **item.model_dump(),
                "decoded": decode_payload(device_type, raw_data, port)
                if raw_data and port is not None
                else None,
            }
        )

    return {
        **response.model_dump(),
        "data_list": decoded,
    }
