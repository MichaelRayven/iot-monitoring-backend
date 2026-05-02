import json
from app.schemas.auth import AuthRequest
from websockets.asyncio.client import ClientConnection
import logging
import asyncio
import websockets
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI

WEBSOCKET_URL = "ws://127.0.0.1:8002"
WEBSOCKET_LOGIN = "root"
WEBSOCKET_PASSWORD = "123"
CONNECTION_RETRY_LIMIT = 3


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - [%(filename)s:%(funcName)s:%(lineno)d]: %(message)s",
)
logger = logging.getLogger(__name__)


async def authenticate_socket(ws: ClientConnection):
    message = AuthRequest(
        login=WEBSOCKET_LOGIN,
        password=WEBSOCKET_PASSWORD,
    )

    await ws.send(message.model_dump_json())
    response = await ws.recv()
    logger.info(response)
    return response


async def connect_socket():
    retries = CONNECTION_RETRY_LIMIT

    while retries > 0:
        try:
            async with websockets.connect(WEBSOCKET_URL) as ws:
                logger.info("Websocket connection success.")
                retries = CONNECTION_RETRY_LIMIT
                await authenticate_socket(ws)

                async for msg in ws:
                    try:
                        data = json.loads(msg)
                    except Exception:
                        data = {"raw": msg}

                    logger.info("Data: ", data)
        except Exception as e:
            retries -= 1
            logger.error("Websocket connection error: ", e)
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_socket()
    yield


app = FastAPI(lifespan=lifespan)
