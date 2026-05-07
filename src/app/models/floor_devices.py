from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class FloorDevice(Base):
    __tablename__ = "floor_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    dev_eui: Mapped[str] = mapped_column(String(16), index=True, unique=True)
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_stationary: Mapped[bool] = mapped_column(nullable=False, default=False)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id"), nullable=False)

    floor = relationship("Floor", back_populates="devices")
