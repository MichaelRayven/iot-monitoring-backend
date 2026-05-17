from typing import Any
from app.services.decoders.base import PayloadDecoderStrategy

class PayloadDecoderService:
    def __init__(self):
        self._strategies: dict[str, PayloadDecoderStrategy] = {}

    def register_strategy(self, device_type: str, strategy: PayloadDecoderStrategy):
        self._strategies[device_type] = strategy

    def decode_payload(
        self, device_type: str | None, payload_hex: str, port: int
    ) -> dict[str, Any]:
        if not device_type:
            return {
                "device": device_type,
                "packet": "unsupported_device_type",
                "payload_hex": payload_hex,
            }

        strategy = self._strategies.get(device_type)

        if not strategy:
            return {
                "device": device_type,
                "packet": "unsupported_device_type",
                "payload_hex": payload_hex,
            }

        return strategy.decode(payload_hex, port)

    def get_supported_devices(self) -> list[str]:
        return list(self._strategies.keys())
