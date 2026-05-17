from typing import Any
from app.services.decoders.base import PayloadDecoderStrategy
from app.services.decoders.utils import read_u8, read_i8, read_u16, read_u32, read_i32


class SmartBadgeDecoder(PayloadDecoderStrategy):
    def decode(self, payload_hex: str, port: int) -> dict[str, Any]:
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
