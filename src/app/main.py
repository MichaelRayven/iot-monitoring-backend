from fastapi.middleware.cors import CORSMiddleware
from app.services.connection_manager import manager
from app.services.payload_decoders import decode_payload
from app.core.settings import settings
from app.services.vega_client import VegaClient
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers.devices import router as devices_router
from app.routers.floors import router as floors_router
from app.routers.buildings import router as buildings_router
from app.routers.realtime import router as realtime_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - [%(filename)s:%(funcName)s:%(lineno)d]: %(message)s",
)
logger = logging.getLogger(__name__)


async def realtime_event_listener(client: VegaClient) -> None:
    async for message in client.listen():
        if message.get("cmd") != "rx":
            continue

        dev_eui = message.get("devEui")
        port = message.get("port")
        raw_data = message.get("data")

        if not dev_eui or port is None or raw_data is None:
            continue

        device_type = message.get("devType") or message.get("device_type")

        decoded = decode_payload(
            device_type=device_type,
            payload_hex=raw_data,
            port=port,
        )

        # await manager.send_update(
        #     dev_eui,
        #     {
        #         "dev_eui": dev_eui,
        #         "port": port,
        #         "raw": message,
        #         "decoded": decoded,
        #     },
        # )


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
            realtime_event_listener(client)
        )

        yield

        app.state.vega_realtime_task.cancel()
        await app.state.vega_client.close()
    except ConnectionRefusedError as _:
        raise ConnectionRefusedError("IoTVegaServer is unreachable at the moment.")


app = FastAPI(lifespan=lifespan, title="Vega IoT Monitoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router)
app.include_router(floors_router)
app.include_router(buildings_router)
app.include_router(realtime_router)
