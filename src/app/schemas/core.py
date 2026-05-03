from pydantic import BaseModel, ConfigDict
from typing import Literal, TypeAlias


class BaseVegaModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    cmd: str


DIRECTIONS = Literal[
    "UPLINK",  # UPLINK - data from device to server,
    "DOWNLINK",  # DOWNLINK – data from server to device,
    "ALL",  # ALL – all data from and to device.
]
DEVICE_ACCESS = Literal["FULL", "SELECTED"]
VegaCommand: TypeAlias = Literal[
    "get_users",
    "manage_users",
    "delete_users",
    "get_device_appdata",
    "get_data",
    "send_data",
    "manage_device_appdata",
    "delete_device_appdata",
    "get_gateways",
    "manage_gateways",
    "delete_gateways",
    "get_devices",
    "manage_devices",
    "delete_devices",
    "get_coverage_map",
    "get_device_downlink_queue",
    "manage_device_downlink_queue",
    "server_info",
    "send_email",
    "tx",
]

COMMAND_LIST: TypeAlias = list[VegaCommand]
DEVICE_PACKET_TYPE = Literal[
    "UNCONF_UP",
    "REPEATUNCONF_UP",
    "UNCONF_DOWN",
    "CONF_UP",
    "REPEATCONF_UP",
    "CONF_DOWN",
    "JOIN_REQ",
    "JOIN_ACC",
    "MAC_LINKCHECK_REQ",
    "MAC_LINKCHECK_ANS",
    "MAC_ADR_REQ",
    "MAC_ADR_ANS",
    "MAC_RXPARAM_REQ",
    "MAC_RXPARAM_ANS",
    "MAC_STATUS_REQ",
    "MAC_STATUS_ANS",
    "MAC_NEWCHAN_REQ",
    "MAC_NEWCHAN_ANS",
    "MAC_RXTIMING_REQ",
    "MAC_RXTIMING_ANS",
    "MAC_TXPARAM_REQ",
    "MAC_TXPARAM_ANS",
    "MAC_DLCHAN_REQ",
    "MAC_DLCHAN_ANS",
]
