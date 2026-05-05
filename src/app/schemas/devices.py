from app.schemas.core import DIRECTIONS, BaseVegaModel
from typing import Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class GetDevicesRequest(BaseVegaModel):
    cmd: Literal["get_devices_req"] = "get_devices_req"

    class Select(BaseModel):
        model_config = ConfigDict(populate_by_name=True, extra="ignore")

        dev_eui_list: list[str] | None = Field(
            default=None,
            alias="devEui_list",
        )
        app_eui_list: list[str] | None = Field(
            default=None,
            alias="appEui_list",
        )

    select: Select | None = None


class DevicePosition(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    longitude: float | None = None
    latitude: float | None = None
    altitude: float | None = None


class DeviceAbpInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    dev_address: int | None = Field(default=None, alias="devAddress")
    apps_key: str | None = Field(default=None, alias="appsKey")
    nwks_key: str | None = Field(default=None, alias="nwksKey")


class DeviceOtaaInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    app_eui: str | None = Field(default=None, alias="appEui")
    app_key: str | None = Field(default=None, alias="appKey")
    last_join_ts: int | None = None


class VegaDevice(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dev_eui: str = Field(alias="devEui")
    dev_name: str | None = Field(default=None, alias="devName")

    abp: DeviceAbpInfo | None = Field(default=None, alias="ABP")
    otaa: DeviceOtaaInfo | None = Field(default=None, alias="OTAA")

    frequency_plan: dict[str, Any] | None = Field(default=None, alias="frequencyPlan")
    channel_mask: dict[str, Any] | None = Field(default=None, alias="channelMask")
    position: DevicePosition | None = None

    device_class: str | None = Field(default=None, alias="class")

    fcnt_up: int | None = None
    fcnt_down: int | None = None
    last_data_ts: int | None = None
    last_rssi: int | None = Field(default=None, alias="lastRssi")
    last_snr: float | None = Field(default=None, alias="lastSnr")

    adr: bool | None = None
    raw_data_storage_period: int | None = Field(
        default=None,
        alias="rawDataStoragePeriod",
    )


class GetDevicesResponse(BaseVegaModel):
    cmd: Literal["get_devices_resp"] = "get_devices_resp"
    status: bool
    err_string: str | None = None
    devices_list: list[VegaDevice] = Field(default_factory=list)


class DeviceDataSelect(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

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


class GetDeviceDataRequest(BaseVegaModel):
    cmd: Literal["get_data_req"] = "get_data_req"
    dev_eui: str = Field(serialization_alias="devEui")
    select: DeviceDataSelect | None = None


class DeviceDataEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

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
