from botocore.exceptions import ValidationError
from app.schemas.vega.realtime import RxPacket
from app.schemas.vega.get_device_data import DeviceDataEntry
from fastapi.middleware.cors import CORSMiddleware
from app.services.connection_manager import manager
from app.core.deps import get_payload_decoder_service
from app.services.payload_decoder_service import PayloadDecoderService
from app.core.settings import settings
from app.services.vega_client import VegaClient
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select

from app.routers.devices import router as devices_router
from app.routers.floors import router as floors_router
from app.routers.buildings import router as buildings_router
from app.routers.realtime import router as realtime_router
from app.routers.floorplan import router as floorplan_router
from app.core.db import SessionLocal
from app.models.floor_devices import FloorDevice
from app.schemas.subscribtions import RealtimeUpdateMessage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - [%(filename)s:%(funcName)s:%(lineno)d]: %(message)s",
)
logger = logging.getLogger(__name__)


async def realtime_event_listener(
    client: VegaClient, decoder_service: PayloadDecoderService
) -> None:
    async for message in client.listen():
        if message.get("cmd") != "rx":
            continue

        try:
            packet = RxPacket.model_validate(message)

            logger.info("Received message: %s", packet.model_dump_json())

            async with SessionLocal() as db:
                stmt = select(FloorDevice).where(FloorDevice.uid == packet.dev_eui)
                result = await db.execute(stmt)
                device = result.scalar_one_or_none()

            logger.info("Device: %s", device)
            if not device:
                continue

            decoded = decoder_service.decode_payload(
                device_type=device.device_type,
                entry=DeviceDataEntry(
                    data=packet.data,
                    port=packet.port,
                    ts=packet.ts,
                    rssi=packet.rssi,
                    snr=packet.snr,
                ),
            )
            logger.info("Decoded message: %s", decoded)

            update_msg = RealtimeUpdateMessage(
                dev_eui=packet.dev_eui,
                floor_id=device.floor_id,
                device_type=device.device_type,
                decoded=decoded,
            )

            await manager.send_update(
                device.floor_id,
                update_msg.model_dump_json(),
            )
        except ValidationError as _:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = VegaClient(
        settings.vega_ws_url,
        settings.vega_ws_login,
        settings.vega_ws_password.get_secret_value(),
    )

    try:
        await client.connect()

        app.state.vega_client = client
        app.state.vega_realtime_task = asyncio.create_task(
            realtime_event_listener(client, get_payload_decoder_service())
        )

        yield

        app.state.vega_realtime_task.cancel()
        await app.state.vega_client.close()
    except ConnectionRefusedError as _:
        raise ConnectionRefusedError("IoTVegaServer is unreachable at the moment.")


app = FastAPI(lifespan=lifespan, title="Vega IoT Monitoring")

app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router)
app.include_router(floors_router)
app.include_router(buildings_router)
app.include_router(realtime_router)
app.include_router(floorplan_router)


@app.post("/test/{floor_id}")
async def test_ws(floor_id: int, body: RealtimeUpdateMessage):
    await manager.send_update(floor_id, body.model_dump_json())
