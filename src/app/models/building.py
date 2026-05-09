from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))

    floors = relationship(
        "Floor",
        back_populates="building",
        cascade="all, delete-orphan",
    )
