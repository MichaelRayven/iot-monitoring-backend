# app/routers/devices.py
from app.schemas.devices import GetDeviceDataRequest
from fastapi import APIRouter, Depends, Request

from app.services.payload_decoders import decode_payload
from app.services.vega_client import VegaClient

router = APIRouter(prefix="/devices", tags=["devices"])


def get_vega_service(request: Request) -> VegaClient:
    return request.app.state.vega_client


@router.get("")
async def get_devices(service: VegaClient = Depends(get_vega_service)):
    return await service.get_devices()


# @router.post("/{dev_eui}/data")
# async def get_device_data(
#     dev_eui: str,
#     payload: GetDeviceDataRequest,
#     device_type: str | None = None,
#     service: VegaClient = Depends(get_vega_service),
# ):
#     response = await service.get_device_data(
#         dev_eui=dev_eui,
#         select=payload.select.model_dump(exclude_none=True),
#     )

#     data_list = response.data_list
#     decoded = []

#     for item in data_list:
#         raw_data = item.data
#         port = item.port

#         decoded.append(
#             {
#                 **item,
#                 "decoded": decode_payload(device_type, raw_data, port)
#                 if raw_data and port is not None
#                 else None,
#             }
#         )

#     return {
#         **response,
#         "data_list": decoded,
#     }
