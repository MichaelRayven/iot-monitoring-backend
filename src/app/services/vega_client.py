from app.schemas.devices import (
    VegaDevice,
    GetDevicesRequest,
    GetDevicesResponse,
    DeviceDataSelect,
    GetDeviceDataResponse,
    GetDeviceDataRequest,
)
from contextlib import suppress
import logging
from app.schemas.auth import (
    AuthRequest,
    AuthResponse,
    AuthCloseRequest,
    AuthCloseResponse,
)
from app.schemas.core import BaseVegaModel
import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection


logger = logging.getLogger(__name__)


class VegaClient:
    def __init__(self, url: str, login: str, password: str) -> None:
        self.url = url
        self.login = login
        self.password = password

        self._ws: ClientConnection | None = None
        self._token: str | None = None

        self._connect_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()

        self._reader_task: asyncio.Task[None] | None = None

        self._pending: set[str] = set()
        self._command_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def connect(self) -> None:
        """Connects to VegaIoTServer websocket with the given url and credentials."""

        async with self._connect_lock:
            if self._ws is not None:
                return

            self._ws = await websockets.connect(self.url)
            self._reader_task = asyncio.create_task(self._reader_loop())

            await self._authenticate()

    async def close(self) -> None:
        if self._ws is None:
            return

        with suppress(Exception):
            await self._deauthenticate()

        if self._reader_task is not None:
            self._reader_task.cancel()

            with suppress(asyncio.CancelledError):
                await self._reader_task

            self._reader_task = None

        await self._ws.close()
        self._ws = None
        self._token = None

    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            yield await self._event_queue.get()

    async def get_devices(self) -> list[VegaDevice]:
        response = await self._request(GetDevicesRequest())
        parsed = GetDevicesResponse.model_validate(response)

        if not parsed.status:
            raise RuntimeError(parsed.err_string or "Failed to get Vega devices")

        return parsed.devices_list

    async def get_device_data(
        self,
        dev_eui: str,
        select: DeviceDataSelect | None = None,
    ) -> GetDeviceDataResponse:
        response = await self._request(
            GetDeviceDataRequest(
                dev_eui=dev_eui,
                select=select or DeviceDataSelect(),
            )
        )

        parsed = GetDeviceDataResponse.model_validate(response)

        if not parsed.status:
            raise RuntimeError(parsed.err_string or "Failed to get Vega device data")

        return parsed

    async def _request(self, payload: BaseVegaModel) -> dict[str, Any]:
        assert self._ws is not None

        async with self._request_lock:
            cmd = self._response_cmd_for(payload.cmd)
            self._pending.add(cmd)

            try:
                await self._ws.send(
                    payload.model_dump_json(by_alias=True, exclude_none=True)
                )

                return await asyncio.wait_for(self._command_queue.get(), timeout=15)
            finally:
                self._pending.discard(cmd)

    async def _reader_loop(self) -> None:
        assert self._ws is not None

        async for raw in self._ws:
            if not isinstance(raw, str):
                continue

            message = json.loads(raw)
            cmd = message.get("cmd")

            logger.info("Message: %s", message)

            if cmd in self._pending:
                await self._command_queue.put(message)
            else:
                await self._event_queue.put(message)

    async def _authenticate(self) -> dict:
        message = AuthRequest(
            login=self.login,
            password=self.password,
        )

        response = await self._request(message)
        auth_response = AuthResponse.model_validate(response)

        if not auth_response.status:
            raise PermissionError(auth_response.err_string)
        else:
            self._token = auth_response.token

        return response

    async def _deauthenticate(self) -> dict:
        assert self._token is not None
        message = AuthCloseRequest(token=self._token)

        response = await self._request(message)
        auth_response = AuthCloseResponse.model_validate(response)

        if not auth_response.status:
            raise PermissionError(auth_response.err_string)
        else:
            self._token = None

        return response

    @staticmethod
    def _response_cmd_for(request_cmd: str) -> str:
        if not request_cmd.endswith("_req"):
            raise ValueError(f"Unsupported request cmd: {request_cmd}")

        return request_cmd.removesuffix("_req") + "_resp"
