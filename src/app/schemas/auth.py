from app.schemas.core import COMMAND_LIST, DIRECTIONS, DEVICE_ACCESS
from typing import Literal
from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    cmd: Literal["auth_req"] = "auth_req"
    login: str
    password: str


class AuthResponse(BaseModel):
    class RxSettings(BaseModel):
        unsolicited: bool
        direction: DIRECTIONS | None
        with_mac_commands: bool | None = Field(validation_alias="withMacCommands")

    cmd: Literal["auth_resp"] = "auth_resp"
    status: bool
    err_string: str | None
    token: str | None
    command_list: COMMAND_LIST | None
    device_access: DEVICE_ACCESS | None
    rx_settings: RxSettings | None


class AuthCloseRequest(BaseModel):
    cmd = "close_auth_req"
    token: str


class AuthCloseResponse(BaseModel):
    cmd = "close_auth_resp"
    status: bool
    err_string: str | None
