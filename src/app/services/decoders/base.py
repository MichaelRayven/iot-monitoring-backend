from abc import ABC, abstractmethod
from typing import Any

class PayloadDecoderStrategy(ABC):
    @abstractmethod
    def decode(self, payload_hex: str, port: int) -> dict[str, Any]:
        """Decode the given payload hex string."""
        pass
