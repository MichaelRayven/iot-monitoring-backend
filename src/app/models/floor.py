from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    building: Mapped[str | None] = mapped_column(String(255), nullable=True)

    floorplan_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    scale_factor: Mapped[float] = mapped_column(Float)

    devices = relationship(
        "FloorDevice",
        back_populates="floor",
        cascade="all, delete-orphan",
    )
