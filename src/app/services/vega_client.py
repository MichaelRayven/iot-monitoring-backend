from app.schemas.vega.auth_close import AuthCloseRequest, AuthCloseResponse
from app.schemas.vega.auth import AuthRequest, AuthResponse
from app.schemas.vega.base import BaseVegaRequest
from app.schemas.vega.get_device_data import (
    GetDeviceDataRequest,
    GetDeviceDataSelect,
    GetDeviceDataResponse,
)
from app.schemas.vega.get_devices import (
    GetDevicesRequest,
    GetDevicesResponse,
    GetDevicesSelect,
    VegaDevice,
)
from contextlib import suppress
import logging
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

        self._expected_response_cmd: str | None = None
        self._expected_dev_eui: str | None = None
        self._response_future: asyncio.Future | None = None

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

    async def get_devices(
        self, select: GetDevicesSelect | None = None
    ) -> GetDevicesResponse:
        response = await self._request(GetDevicesRequest(select=select))
        return GetDevicesResponse.model_validate(response)

    async def get_device_by_id(self, dev_eui: str) -> VegaDevice | None:
        """Get single device registration info by EUI"""

        response = await self.get_devices(
            GetDevicesSelect(
                dev_eui_list=[dev_eui]  # ty:ignore[unknown-argument]
            )
        )

        if response.status and len(response.devices_list) > 0:
            return response.devices_list[0]
        else:
            return None

    async def get_device_data(
        self,
        dev_eui: str,
        select: GetDeviceDataSelect | None = GetDeviceDataSelect(direction="UPLINK"),
    ) -> GetDeviceDataResponse:
        response = await self._request(
            GetDeviceDataRequest(
                dev_eui=dev_eui,
                select=select,
            )
        )

        return GetDeviceDataResponse.model_validate(response)

    async def _request(self, payload: BaseVegaRequest) -> dict[str, Any]:
        assert self._ws is not None

        async with self._request_lock:
            cmd = self._response_cmd_for(payload.cmd)
            self._expected_response_cmd = cmd

            payload_dict = payload.model_dump(by_alias=True, exclude_none=True)
            self._expected_dev_eui = payload_dict.get("devEui")

            self._response_future = asyncio.get_running_loop().create_future()

            try:
                logger.debug(
                    "Request structure: %s",
                    payload.model_dump_json(by_alias=True, exclude_none=True),
                )
                await self._ws.send(
                    payload.model_dump_json(by_alias=True, exclude_none=True)
                )

                return await asyncio.wait_for(self._response_future, timeout=15)
            finally:
                self._expected_response_cmd = None
                self._expected_dev_eui = None
                self._response_future = None

    async def _reader_loop(self) -> None:
        assert self._ws is not None

        async for raw in self._ws:
            if not isinstance(raw, str):
                continue

            message = json.loads(raw)
            cmd = message.get("cmd")

            is_expected = False
            if cmd and cmd == self._expected_response_cmd:
                is_expected = True

                if self._expected_dev_eui is not None:
                    msg_dev_eui = message.get("devEui")
                    if msg_dev_eui is not None and msg_dev_eui != self._expected_dev_eui:
                        is_expected = False

            if is_expected and self._response_future and not self._response_future.done():
                logger.info("Command matched expected: %s", cmd)
                self._response_future.set_result(message)
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
