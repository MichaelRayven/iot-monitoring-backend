from app.schemas.core import COMMAND_LIST, DIRECTIONS, DEVICE_ACCESS, BaseVegaModel
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class AuthRequest(BaseVegaModel):
    cmd: Literal["auth_req"] = "auth_req"
    login: str
    password: str


class AuthResponse(BaseVegaModel):
    class RxSettings(BaseModel):
        model_config = ConfigDict(
            populate_by_name=True,
            extra="ignore",
        )

        unsolicited: bool
        direction: DIRECTIONS | None = None
        with_mac_commands: bool | None = Field(
            default=None, validation_alias="withMacCommands"
        )

    cmd: Literal["auth_resp"] = "auth_resp"
    status: bool
    err_string: str | None = None
    token: str | None = None
    command_list: COMMAND_LIST = Field(default_factory=list)
    device_access: DEVICE_ACCESS | None = None
    rx_settings: RxSettings | None = None


class AuthCloseRequest(BaseVegaModel):
    cmd: Literal["close_auth_req"] = "close_auth_req"
    token: str


class AuthCloseResponse(BaseVegaModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    cmd: Literal["close_auth_resp"] = "close_auth_resp"
    status: bool
    err_string: str | None = None
