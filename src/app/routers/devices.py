import logging
from app.schemas.device import DeviceResponse
from app.core.deps import VegaClientDep, PayloadDecoderServiceDep
from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["devices"])



@router.get("/types", response_model=list[str])
async def get_device_types(decoder_service: PayloadDecoderServiceDep):
    return decoder_service.get_supported_devices()

@router.get("", response_model=list[DeviceResponse])
async def get_devices(service: VegaClientDep):
    response = await service.get_devices()

    if not response.status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device list from IoTVegaServer.",
        )

    result: list[DeviceResponse] = [
        DeviceResponse(
            dev_eui=device.dev_eui,
            name=device.name,
            rssi=device.last_rssi,
            snr=device.last_snr,
            last_data_ts=device.last_data_ts,
        )
        for device in response.devices_list
    ]
    logger.info(result)

    return result
