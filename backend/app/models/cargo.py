import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BodyType

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.company import Company


class CargoStatus(str, enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Cargo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cargo"

    shipper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    reference_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    weight_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    required_body_type: Mapped[BodyType | None] = mapped_column(Enum(BodyType, name="body_type"))

    origin_address: Mapped[str] = mapped_column(String(512), nullable=False)
    origin_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    destination_address: Mapped[str] = mapped_column(String(512), nullable=False)
    destination_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )

    pickup_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[CargoStatus] = mapped_column(
        Enum(CargoStatus, name="cargo_status"), nullable=False, default=CargoStatus.NEW
    )

    shipper: Mapped["Company"] = relationship(back_populates="cargo")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="cargo")
