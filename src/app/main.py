# from app.services.realtime_hub import hub
# from app.services.payload_decoders import decode_payload
from app.core.settings import settings
from app.services.vega_client import VegaClient
import logging
import asyncio
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - [%(filename)s:%(funcName)s:%(lineno)d]: %(message)s",
)
logger = logging.getLogger(__name__)


async def realtime_event_listener(client: VegaClient) -> None:
    await client.connect()

    async for message in client.listen():
        logger.info("Realtime message: %s", message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = VegaClient(
        settings.vega_ws_url,
        settings.vega_ws_login,
        settings.vega_ws_password.get_secret_value(),
    )
    app.state.vega_client = client
    app.state.vega_realtime_task = asyncio.create_task(realtime_event_listener(client))

    yield

    app.state.vega_realtime_task.cancel()
    await app.state.vega_client.close()


app = FastAPI(lifespan=lifespan, title="Vega IoT Monitoring")
