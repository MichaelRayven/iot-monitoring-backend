from app.schemas.core import DIRECTIONS, DEVICE_PACKET_TYPE
from typing import Literal, get_args
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DeviceDataRequest(BaseModel):
    class DeviceDataRequestFilters(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        date_from: int | None
        date_to: int | None
        begin_index: int = Field(description="Begin index of data list", default=0)
        limit: int = Field(description="Limit of response data list", default=1000)
        port: int | None
        direction: DIRECTIONS | None
        with_mac_commands: bool | None = Field(
            default=None,
            validation_alias="withMacCommands",
        )

    cmd: Literal["get_data_req"] = "get_data_req"
    dev_eui: str = Field(validation_alias="devEui")
    select: DeviceDataRequestFilters | None


class DeviceDataResponse(BaseModel):
    class DeviceDataEntry(BaseModel):
        timestamp: int = Field(validation_alias="ts")
        gateway_id: str = Field(validation_alias="gatewayId")
        ack: bool
        frame_counter: int = Field(validation_alias="fcnt")
        port: int
        data: str  # TODO: Parse this bullshit
        mac_data: str | None = Field(default=None, validation_alias="macData")
        frequency: int = Field(validation_alias="freq")
        rssi: int | None = None
        snr: float | None = None
        type: list[DEVICE_PACKET_TYPE]
        packet_status: str | None = Field(default=None, validation_alias="packetStatus")

        @field_validator("type", mode="before")
        @classmethod
        def validate_type(cls, value: str) -> list[DEVICE_PACKET_TYPE]:
            result = value.split("+")
            allowed = get_args(DEVICE_PACKET_TYPE)

            for item in result:
                if item not in allowed:
                    raise ValueError(f"{item} is not an accepted packet type")

            return result  # ty:ignore[invalid-return-type]

    cmd: Literal["get_data_resp"] = "get_data_resp"
    status: bool
    err_string: str | None = None
    dev_eui: str = Field(validation_alias="devEui")
    app_eui: str = Field(validation_alias="appEui")
    direction: DIRECTIONS | None = None
    total_num: int | None = Field(default=None, validation_alias="totalNum")
    data_list: list[DeviceDataEntry] | None = None
