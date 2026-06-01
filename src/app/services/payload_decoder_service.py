from typing import Any

from app.schemas.vega.get_device_data import DeviceDataEntry
from app.services.decoders.base import PayloadDecoderStrategy


class PayloadDecoderService:
    def __init__(self) -> None:
        self._strategies: dict[str, PayloadDecoderStrategy] = {}

    def register_strategy(self, device_type: str, strategy: PayloadDecoderStrategy) -> None:
        self._strategies[device_type] = strategy

    def decode_payload(
        self, device_type: str, entry: DeviceDataEntry
    ) -> dict[str, Any]:
        """
        Decode a Vega data entry using the registered strategy for *device_type*.

        The Vega server's ``entry.ts`` is injected into the returned dict as ``"ts"``
        so callers always get the authoritative network timestamp instead of the
        (often inaccurate) device-internal clock.
        """
        result: dict[str, Any]

        if not device_type or not entry.data or entry.port is None:
            result = {
                "device": device_type,
                "packet": "unsupported_device_type",
                "payload_hex": entry.data,
            }
        else:
            strategy = self._strategies.get(device_type)
            if not strategy:
                result = {
                    "device": device_type,
                    "packet": "unsupported_device_type",
                    "payload_hex": entry.data,
                }
            else:
                result = strategy.decode(entry.data, entry.port)

        # Override the (inaccurate) device-internal timestamp with the
        # authoritative Vega server timestamp.
        result["device_timestamp"] = entry.ts
        return result

    def get_supported_devices(self) -> list[str]:
        return list(self._strategies.keys())
