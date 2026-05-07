from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.building import Building  # noqa: F401


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    floorplan_key: Mapped[str] = mapped_column(String(1024))
    scale_factor: Mapped[int] = mapped_column(Integer)

    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"), nullable=False)

    building = relationship("Building", back_populates="floors")
    devices = relationship(
        "FloorDevice",
        back_populates="floor",
        cascade="all, delete-orphan",
    )
