from typing import Any
from app.services.decoders.base import PayloadDecoderStrategy
from app.services.decoders.utils import read_u8, read_i8, read_u32


class SmartMS0101Decoder(PayloadDecoderStrategy):
    def decode(self, payload_hex: str, port: int) -> dict[str, Any]:
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
