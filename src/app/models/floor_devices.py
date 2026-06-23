from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

BEACON_DEVICE_TYPE = "Beacon"


class FloorDevice(Base):
    __tablename__ = "floor_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    # Unified hardware identifier:
    #   vega   → dev_eui  (16-char hex, e.g. "0102030405060708")
    #   beacon → mac_address (colon-separated, e.g. "AA:BB:CC:DD:EE:FF")
    uid: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)

    # "Beacon" for BLE beacons; any other value is a Vega LoRaWAN device type
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_stationary: Mapped[bool] = mapped_column(nullable=False, default=False)

    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id"), nullable=False)
    floor = relationship("Floor", back_populates="devices")

    @property
    def is_beacon(self) -> bool:
        return self.device_type == BEACON_DEVICE_TYPE
