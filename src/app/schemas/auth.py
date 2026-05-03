from app.schemas.core import COMMAND_LIST, DIRECTIONS, DEVICE_ACCESS, BaseVegaModel
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class AuthRequest(BaseVegaModel):
    cmd: Literal["auth_req"] = "auth_req"
    login: str
    password: str


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class RxSettings(BaseModel):
        model_config = ConfigDict(
            populate_by_name=True,
            extra="ignore",
        )

        unsolicited: bool
        direction: DIRECTIONS | None = None
        with_mac_commands: bool | None = Field(validation_alias="withMacCommands")

    cmd: Literal["auth_resp"] = "auth_resp"
    status: bool
    err_string: str | None = None
    token: str | None = None
    command_list: COMMAND_LIST = Field(default_factory=list)
    device_access: DEVICE_ACCESS | None
    rx_settings: RxSettings | None


class AuthCloseRequest(BaseVegaModel):
    cmd: Literal["close_auth_req"] = "close_auth_req"
    token: str


class AuthCloseResponse(BaseModel):
    cmd: Literal["close_auth_resp"] = "close_auth_resp"
    status: bool
    err_string: str | None = None
