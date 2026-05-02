from enum import IntEnum, IntFlag
from struct import unpack_from
from typing import Literal

from pydantic import BaseModel


# =========================================================
# Common enums
# =========================================================


class PacketType(IntEnum):
    SETTINGS = 0
    GPS = 1
    BLE_SINGLE = 2
    BLE_TRIPLE = 5


class PacketReason(IntEnum):
    TIME = 0
    MOTION_START = 1
    MOTION_STOP = 2
    TAMPER = 3
    FALL = 4
    SEARCH_ALARM = 5
    TAG_LOSS = 6


class BeaconType(IntEnum):
    NONE = 0
    IBEACON = 1
    EDDYSTONE = 2
    ALTBEACON = 3
    VEGA = 4


class LocationMethod(IntEnum):
    GPS = 1
    BLE = 2
    BLE_GPS = 3


class AccelerometerSensitivity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    DISABLED = 4


class ActiveCommand(IntEnum):
    NONE = 0
    CALL = 1
    WARNING = 2
    SEARCH = 3
    CANCEL = 4


class BadgeFlags(IntFlag):
    MOVING = 1 << 0
    FALL_DETECTED = 1 << 1
    COORDINATES_VALID = 1 << 2


# =========================================================
# Shared structures
# =========================================================


class PacketHeader(BaseModel):
    packet_type: PacketType

    reason: PacketReason

    battery_percent: int

    timestamp: int

    temperature: int

    flags_raw: int

    vertical_angle: int

    moving: bool

    fall_detected: bool

    coordinates_valid: bool

    active_command: ActiveCommand


class BasePacket(BaseModel):
    header: PacketHeader


# =========================================================
# Packet Type 1 — GPS packet
# =========================================================


class GpsPacket(BasePacket):
    packet_type: Literal[PacketType.GPS] = PacketType.GPS

    latitude: float

    longitude: float

    course: int

    speed_kmh: int

    altitude: int

    satellites_visible: int

    satellites_used: int

    tag_state_raw: int


# =========================================================
# Packet Type 2 — Single BLE beacon
# =========================================================


class BleSinglePacket(BasePacket):
    packet_type: Literal[PacketType.BLE_SINGLE] = PacketType.BLE_SINGLE

    beacon_type: BeaconType

    beacon_data: bytes

    reference_rssi: int

    tx_power: int

    tag_state_raw: int


# =========================================================
# Packet Type 5 — Three nearest Vega BLE beacons
# =========================================================


class VegaBeacon(BaseModel):
    mac_address: str

    battery_percent: int

    temperature: int

    humidity: int

    reference_rssi: int

    tx_power: int


class BleTriplePacket(BasePacket):
    packet_type: Literal[PacketType.BLE_TRIPLE] = PacketType.BLE_TRIPLE

    beacons: list[VegaBeacon]

    tag_state_raw: int


# =========================================================
# Packet Type 0 — Settings packet
# =========================================================


class SettingId(IntEnum):
    CONFIRMED_UPLINKS = 4
    ADR = 5
    RETRIES = 8
    TRANSMIT_PERIOD = 16
    ACCELEROMETER_SENSITIVITY = 44
    DATA_COLLECTION_PERIOD = 49
    MOTION_ACCUMULATION_PERIOD = 62
    MOTION_TRANSMIT_PERIOD = 63
    MOTION_ALARM = 71
    LOCATION_METHOD = 240


class SettingsEntry(BaseModel):
    parameter_id: SettingId

    value_length: int

    raw_value: bytes

    parsed_value: int | bool | str | None = None


class SettingsPacket(BaseModel):
    packet_type: Literal[PacketType.SETTINGS] = PacketType.SETTINGS

    settings: list[SettingsEntry]


# =========================================================
# Parsing helpers
# =========================================================


def parse_header(raw: bytes) -> tuple[PacketHeader, int]:
    offset = 0

    packet_type = PacketType(raw[offset])
    offset += 1

    reason = PacketReason(raw[offset])
    offset += 1

    battery_percent = raw[offset]
    offset += 1

    timestamp = unpack_from("<I", raw, offset)[0]
    offset += 4

    temperature = unpack_from("<b", raw, offset)[0]
    offset += 1

    flags_raw = raw[offset]
    offset += 1

    vertical_angle = unpack_from("<H", raw, offset)[0]
    offset += 2

    moving = bool(flags_raw & (1 << 0))

    fall_detected = bool(flags_raw & (1 << 1))

    coordinates_valid = bool(flags_raw & (1 << 2))

    active_command = ActiveCommand((flags_raw >> 3) & 0b111)

    return (
        PacketHeader(
            packet_type=packet_type,
            reason=reason,
            battery_percent=battery_percent,
            timestamp=timestamp,
            temperature=temperature,
            flags_raw=flags_raw,
            vertical_angle=vertical_angle,
            moving=moving,
            fall_detected=fall_detected,
            coordinates_valid=coordinates_valid,
            active_command=active_command,
        ),
        offset,
    )


def format_mac(data: bytes) -> str:
    return ":".join(f"{b:02X}" for b in data)


# =========================================================
# GPS decoder
# =========================================================


def decode_gps_packet(payload_hex: str) -> GpsPacket:
    raw = bytes.fromhex(payload_hex)

    header, offset = parse_header(raw)

    latitude_raw = unpack_from("<i", raw, offset)[0]
    offset += 4

    longitude_raw = unpack_from("<i", raw, offset)[0]
    offset += 4

    course = unpack_from("<H", raw, offset)[0]
    offset += 2

    speed_kmh = unpack_from("<H", raw, offset)[0]
    offset += 2

    altitude = unpack_from("<h", raw, offset)[0]
    offset += 2

    satellites_visible = raw[offset]
    offset += 1

    satellites_used = raw[offset]
    offset += 1

    tag_state_raw = raw[offset]

    return GpsPacket(
        header=header,
        latitude=latitude_raw / 1_000_000,
        longitude=longitude_raw / 1_000_000,
        course=course,
        speed_kmh=speed_kmh,
        altitude=altitude,
        satellites_visible=satellites_visible,
        satellites_used=satellites_used,
        tag_state_raw=tag_state_raw,
    )


# =========================================================
# BLE single decoder
# =========================================================


def decode_ble_single_packet(payload_hex: str) -> BleSinglePacket:
    raw = bytes.fromhex(payload_hex)

    header, offset = parse_header(raw)

    beacon_type = BeaconType(raw[offset])
    offset += 1

    beacon_data = raw[offset : offset + 20]
    offset += 20

    reference_rssi = unpack_from("<b", raw, offset)[0]
    offset += 1

    tx_power = unpack_from("<b", raw, offset)[0]
    offset += 1

    tag_state_raw = raw[offset]

    return BleSinglePacket(
        header=header,
        beacon_type=beacon_type,
        beacon_data=beacon_data,
        reference_rssi=reference_rssi,
        tx_power=tx_power,
        tag_state_raw=tag_state_raw,
    )


# =========================================================
# BLE triple decoder
# =========================================================


def decode_ble_triple_packet(payload_hex: str) -> BleTriplePacket:
    raw = bytes.fromhex(payload_hex)

    header, offset = parse_header(raw)

    beacons: list[VegaBeacon] = []

    for _ in range(3):
        mac_raw = raw[offset : offset + 6]
        offset += 6

        battery = raw[offset]
        offset += 1

        temperature = unpack_from("<b", raw, offset)[0]
        offset += 1

        humidity = raw[offset]
        offset += 1

        reference_rssi = unpack_from("<b", raw, offset)[0]
        offset += 1

        tx_power = unpack_from("<b", raw, offset)[0]
        offset += 1

        beacons.append(
            VegaBeacon(
                mac_address=format_mac(mac_raw),
                battery_percent=battery,
                temperature=temperature,
                humidity=humidity,
                reference_rssi=reference_rssi,
                tx_power=tx_power,
            )
        )

    tag_state_raw = raw[offset]

    return BleTriplePacket(
        header=header,
        beacons=beacons,
        tag_state_raw=tag_state_raw,
    )


# =========================================================
# Settings packet decoder
# =========================================================


def parse_setting_value(
    parameter_id: SettingId,
    raw_value: bytes,
) -> int | bool | str:
    value = raw_value[0]

    match parameter_id:
        case SettingId.CONFIRMED_UPLINKS:
            return value == 1

        case SettingId.ADR:
            return value == 1

        case SettingId.RETRIES:
            return value

        case SettingId.ACCELEROMETER_SENSITIVITY:
            return AccelerometerSensitivity(value).name

        case SettingId.LOCATION_METHOD:
            return LocationMethod(value).name

        case _:
            return value


def decode_settings_packet(payload_hex: str) -> SettingsPacket:
    raw = bytes.fromhex(payload_hex)

    offset = 1

    settings: list[SettingsEntry] = []

    while offset < len(raw):
        parameter_id_raw = unpack_from("<H", raw, offset)[0]
        offset += 2

        value_length = raw[offset]
        offset += 1

        raw_value = raw[offset : offset + value_length]
        offset += value_length

        parameter_id = SettingId(parameter_id_raw)

        parsed_value = parse_setting_value(
            parameter_id,
            raw_value,
        )

        settings.append(
            SettingsEntry(
                parameter_id=parameter_id,
                value_length=value_length,
                raw_value=raw_value,
                parsed_value=parsed_value,
            )
        )

    return SettingsPacket(settings=settings)


# =========================================================
# Dispatcher
# =========================================================


DecodedPacket = GpsPacket | BleSinglePacket | BleTriplePacket | SettingsPacket


def decode_packet(payload_hex: str) -> DecodedPacket:
    raw = bytes.fromhex(payload_hex)

    packet_type = PacketType(raw[0])

    match packet_type:
        case PacketType.GPS:
            return decode_gps_packet(payload_hex)

        case PacketType.BLE_SINGLE:
            return decode_ble_single_packet(payload_hex)

        case PacketType.BLE_TRIPLE:
            return decode_ble_triple_packet(payload_hex)

        case PacketType.SETTINGS:
            return decode_settings_packet(payload_hex)

        case _:
            raise ValueError(f"Unsupported packet type: {packet_type}")
