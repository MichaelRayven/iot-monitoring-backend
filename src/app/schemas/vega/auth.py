from app.schemas.vega.base import (
    COMMAND_LIST,
    DIRECTIONS,
    DEVICE_ACCESS,
    BaseVegaModel,
    BaseVegaRequest,
)
from typing import Literal
from pydantic import Field


class AuthRequest(BaseVegaRequest):
    cmd: Literal["auth_req"] = "auth_req"
    login: str
    password: str


class AuthResponse(BaseVegaModel):
    cmd: Literal["auth_resp"] = "auth_resp"

    class RxSettings(BaseVegaModel):
        unsolicited: bool
        direction: DIRECTIONS | None = None
        with_mac_commands: bool | None = Field(default=None, alias="withMacCommands")

    status: bool
    err_string: str | None = None
    token: str | None = None
    command_list: COMMAND_LIST = Field(default_factory=list)
    device_access: DEVICE_ACCESS | None = None
    rx_settings: RxSettings | None = None
