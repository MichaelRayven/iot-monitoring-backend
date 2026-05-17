from typing import Any
from app.services.decoders.base import PayloadDecoderStrategy
from app.services.decoders.utils import read_u8, read_i8, read_u32


class SmartWB0101Decoder(PayloadDecoderStrategy):
    def decode(self, payload_hex: str, port: int) -> dict[str, Any]:
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
