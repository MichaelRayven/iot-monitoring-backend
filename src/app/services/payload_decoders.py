from typing import Any


def read_u8(data: bytes, offset: int) -> tuple[int, int]:
    return data[offset], offset + 1


def read_i8(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 1], "little", signed=True)
    return value, offset + 1


def read_u16(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 2], "little")
    return value, offset + 2


def read_i16(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 2], "little", signed=True)
    return value, offset + 2


def read_u32(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 4], "little")
    return value, offset + 4


def read_i32(data: bytes, offset: int) -> tuple[int, int]:
    value = int.from_bytes(data[offset : offset + 4], "little", signed=True)
    return value, offset + 4


def decode_smart_wb0101(payload_hex: str, port: int) -> dict[str, Any]:
    data = bytes.fromhex(payload_hex)

    if port != 2 or len(data) < 7:
        return {"packet": "unknown", "payload_hex": payload_hex}

    offset = 0
    mode, offset = read_u8(data, offset)
    battery, offset = read_u8(data, offset)
    timestamp, offset = read_u32(data, offset)
    temperature, offset = read_i8(data, offset)

    modes = {
        1: "waiting",
        2: "alarm_transmission",
        3: "alarm_received_by_server",
        4: "alarm_cancelled",
        5: "alarm_accepted_by_operator",
        6: "simple_press",
    }

    return {
        "device": "Smart-WB0101",
        "packet": "button_state",
        "mode": mode,
        "mode_label": modes.get(mode, "unknown"),
        "battery_percent": battery,
        "device_timestamp": timestamp,
        "temperature_c": temperature,
    }


def decode_smart_ms0101(payload_hex: str, port: int) -> dict[str, Any]:
    data = bytes.fromhex(payload_hex)

    if port != 2 or len(data) < 8:
        return {"packet": "unknown", "payload_hex": payload_hex}

    offset = 0
    packet_type, offset = read_u8(data, offset)
    battery, offset = read_u8(data, offset)
    settings, offset = read_u8(data, offset)
    temperature, offset = read_i8(data, offset)
    reason, offset = read_u8(data, offset)
    timestamp, offset = read_u32(data, offset)

    return {
        "device": "Smart-MS0101",
        "packet": "motion_sensor_state",
        "packet_type": packet_type,
        "battery_percent": battery,
        "settings_raw": settings,
        "activation_type": "OTAA" if settings & 0b00000001 == 0 else "ABP",
        "confirmation_enabled": bool(settings & 0b00000010),
        "temperature_c": temperature,
        "send_reason": reason,
        "device_timestamp": timestamp,
    }


def decode_smart_badge(payload_hex: str, port: int) -> dict[str, Any]:
    data = bytes.fromhex(payload_hex)

    if port != 2 or len(data) < 2:
        return {"packet": "unknown", "payload_hex": payload_hex}

    offset = 0
    packet_type, offset = read_u8(data, offset)

    if packet_type == 1:
        reason, offset = read_u8(data, offset)
        battery, offset = read_u8(data, offset)
        timestamp, offset = read_u32(data, offset)
        temperature, offset = read_i8(data, offset)
        state, offset = read_u8(data, offset)
        tilt_angle, offset = read_u16(data, offset)
        latitude_raw, offset = read_i32(data, offset)
        longitude_raw, offset = read_i32(data, offset)

        return {
            "device": "Smart Badge",
            "packet": "gnss_position",
            "reason": reason,
            "battery_percent": battery,
            "device_timestamp": timestamp,
            "temperature_c": temperature,
            "state_raw": state,
            "tilt_angle": tilt_angle,
            "latitude": latitude_raw / 1_000_000,
            "longitude": longitude_raw / 1_000_000,
        }

    if packet_type == 2:
        reason, offset = read_u8(data, offset)
        battery, offset = read_u8(data, offset)
        timestamp, offset = read_u32(data, offset)
        temperature, offset = read_i8(data, offset)
        state, offset = read_u8(data, offset)
        tilt_angle, offset = read_u16(data, offset)
        beacon_type, offset = read_u8(data, offset)

        return {
            "device": "Smart Badge",
            "packet": "nearest_ble_beacon",
            "reason": reason,
            "battery_percent": battery,
            "device_timestamp": timestamp,
            "temperature_c": temperature,
            "state_raw": state,
            "tilt_angle": tilt_angle,
            "beacon_type": beacon_type,
            "rest_payload_hex": data[offset:].hex(),
        }

    if packet_type == 5:
        reason, offset = read_u8(data, offset)
        battery, offset = read_u8(data, offset)
        timestamp, offset = read_u32(data, offset)
        temperature, offset = read_i8(data, offset)
        state, offset = read_u8(data, offset)
        tilt_angle, offset = read_u16(data, offset)

        beacons = []
        for index in range(3):
            if offset + 9 > len(data):
                break

            mac_or_id = data[offset : offset + 6].hex()
            offset += 6

            beacon_battery, offset = read_u8(data, offset)
            beacon_temperature, offset = read_i8(data, offset)
            humidity, offset = read_u8(data, offset)

            beacons.append(
                {
                    "index": index + 1,
                    "mac_or_id": mac_or_id,
                    "battery_percent": beacon_battery,
                    "temperature_c": beacon_temperature,
                    "humidity_percent": humidity,
                }
            )

        return {
            "device": "Smart Badge",
            "packet": "three_nearest_ble_beacons",
            "reason": reason,
            "battery_percent": battery,
            "device_timestamp": timestamp,
            "temperature_c": temperature,
            "state_raw": state,
            "tilt_angle": tilt_angle,
            "beacons": beacons,
        }

    return {
        "device": "Smart Badge",
        "packet": "unknown_badge_packet",
        "packet_type": packet_type,
        "payload_hex": payload_hex,
    }


def decode_payload(
    device_type: str | None, payload_hex: str, port: int
) -> dict[str, Any]:
    normalized = (device_type or "").lower()

    if "wb0101" in normalized:
        return decode_smart_wb0101(payload_hex, port)

    if "ms0101" in normalized:
        return decode_smart_ms0101(payload_hex, port)

    if "badge" in normalized:
        return decode_smart_badge(payload_hex, port)

    return {
        "device": device_type,
        "packet": "unsupported_device_type",
        "payload_hex": payload_hex,
    }
