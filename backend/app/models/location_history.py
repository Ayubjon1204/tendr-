from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.truck import Truck


class LocationHistory(Base):
    __tablename__ = "location_history"
    __table_args__ = (
        Index("ix_location_history_truck_time", "truck_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    truck_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("trucks.id", ondelete="CASCADE"), nullable=False
    )
    lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    heading: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    truck: Mapped["Truck"] = relationship(back_populates="location_history")
