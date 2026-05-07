from typing import Literal
from app.schemas.vega.base import BaseVegaModel, BaseVegaRequest


class AuthCloseRequest(BaseVegaRequest):
    cmd: Literal["close_auth_req"] = "close_auth_req"
    token: str


class AuthCloseResponse(BaseVegaModel):
    cmd: Literal["close_auth_resp"] = "close_auth_resp"
    status: bool
    err_string: str | None = None
