import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
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


class Truck(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "trucks"

    carrier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
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
    current_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    home_base_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    carrier: Mapped["Company"] = relationship(back_populates="trucks")
    drivers: Mapped[list["Driver"]] = relationship(back_populates="current_truck")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="truck")
    schedules: Mapped[list["TruckSchedule"]] = relationship(back_populates="truck")
    location_history: Mapped[list["LocationHistory"]] = relationship(back_populates="truck")
