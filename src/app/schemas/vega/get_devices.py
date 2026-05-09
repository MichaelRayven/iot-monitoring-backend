from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from app.schemas.vega.base import BaseVegaModel, BaseVegaRequest


class GetDevicesRequest(BaseVegaRequest):
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


class DevicePosition(BaseVegaModel):
    longitude: float | None = None
    latitude: float | None = None
    altitude: float | None = None


class AbpInfo(BaseVegaModel):
    dev_address: int | None = Field(default=None, alias="devAddress")
    apps_key: str | None = Field(default=None, alias="appsKey")
    nwks_key: str | None = Field(default=None, alias="nwksKey")


class OtaaInfo(BaseVegaModel):
    app_eui: str | None = Field(default=None, alias="appEui")
    app_key: str | None = Field(default=None, alias="appKey")
    last_join_ts: int | None = None


class VegaDevice(BaseVegaModel):
    dev_eui: str = Field(alias="devEui")
    dev_name: str | None = Field(default=None, alias="devName")

    abp: AbpInfo | None = Field(default=None, alias="ABP")
    otaa: OtaaInfo | None = Field(default=None, alias="OTAA")

    frequency_plan: dict[str, float] | None = Field(default=None, alias="frequencyPlan")
    channel_mask: dict[str, bool] | None = Field(default=None, alias="channelMask")
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
