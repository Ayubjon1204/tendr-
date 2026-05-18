import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BodyType

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.company import Company
    from app.models.driver import Driver
    from app.models.location_history import LocationHistory
    from app.models.truck_schedule import TruckSchedule


class TruckStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    LOADING = "loading"
    UNLOADING = "unloading"
    MAINTENANCE = "maintenance"
    OFF_DUTY = "off_duty"


class SpotSource(str, enum.Enum):
    """"Ko'cha"dan topilgan mashinaning manbai."""
    LORRY = "lorry"          # Lorry dasturidan
    TELEGRAM = "telegram"    # Telegram guruhdan
    MANUAL = "manual"        # Boshqacha qo'lda kiritildi


class Truck(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "trucks"

    # Carrier'ning ro'yxatga olingan mashinasi bo'lsa, carrier_id to'liq.
    # Spot truck bo'lsa, carrier_id NULL.
    carrier_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT")
    )

    is_spot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spot_source: Mapped[SpotSource | None] = mapped_column(Enum(SpotSource, name="spot_source"))
    spot_added_by_company_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="SET NULL")
    )

    plate_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    capacity_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    body_type: Mapped[BodyType] = mapped_column(
        Enum(BodyType, name="body_type"), nullable=False, default=BodyType.TENT
    )
    status: Mapped[TruckStatus] = mapped_column(
        Enum(TruckStatus, name="truck_status"),
        nullable=False,
        default=TruckStatus.AVAILABLE,
    )

    current_lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    current_lng: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    home_base_lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    home_base_lng: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    carrier: Mapped["Company | None"] = relationship(
        back_populates="trucks", foreign_keys=[carrier_id]
    )
    drivers: Mapped[list["Driver"]] = relationship(back_populates="current_truck")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="truck")
    schedules: Mapped[list["TruckSchedule"]] = relationship(back_populates="truck")
    location_history: Mapped[list["LocationHistory"]] = relationship(back_populates="truck")

    @property
    def current_location(self) -> dict[str, float] | None:
        if self.current_lat is None or self.current_lng is None:
            return None
        return {"lat": float(self.current_lat), "lng": float(self.current_lng)}

    @property
    def home_base_location(self) -> dict[str, float] | None:
        if self.home_base_lat is None or self.home_base_lng is None:
            return None
        return {"lat": float(self.home_base_lat), "lng": float(self.home_base_lng)}
