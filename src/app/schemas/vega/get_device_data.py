from typing import Literal
from pydantic import Field
from app.schemas.vega.base import BaseVegaModel, DIRECTIONS, BaseVegaRequest


class GetDeviceDataSelect(BaseVegaModel):
    date_from: int | None = None
    date_to: int | None = None
    begin_index: int = 0
    limit: int = 1000
    port: int | None = None
    direction: DIRECTIONS | None = None
    with_mac_commands: bool | None = Field(
        default=None,
        alias="withMacCommands",
    )


class GetDeviceDataRequest(BaseVegaRequest):
    cmd: Literal["get_data_req"] = "get_data_req"

    dev_eui: str = Field(serialization_alias="devEui")
    select: GetDeviceDataSelect | None = None


class DeviceDataEntry(BaseVegaModel):
    ts: int | None = None

    gateway_id: str | None = Field(default=None, alias="gatewayId")
    ack: bool | None = None
    fcnt: int | None = None
    port: int | None = None
    data: str | None = None
    mac_data: str | None = Field(default=None, alias="macData")

    freq: int | None = None
    dr: str | None = None
    rssi: int | None = None
    snr: float | None = None

    type: str | None = None
    packet_status: str | None = Field(default=None, alias="packetStatus")


class GetDeviceDataResponse(BaseVegaModel):
    cmd: Literal["get_data_resp"] = "get_data_resp"
    status: bool
    err_string: str | None = None

    dev_eui: str | None = Field(default=None, alias="devEui")
    app_eui: str | None = Field(default=None, alias="appEui")
    direction: DIRECTIONS | None = None
    total_num: int | None = Field(default=None, alias="totalNum")

    data_list: list[DeviceDataEntry] = Field(default_factory=list)
