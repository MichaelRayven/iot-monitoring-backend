from app.core.deps import VegaClientDep
from fastapi import APIRouter

from app.services.payload_decoders import decode_payload

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("")
async def get_devices(service: VegaClientDep):
    return await service.get_devices()


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
