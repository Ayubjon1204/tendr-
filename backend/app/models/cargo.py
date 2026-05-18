import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BodyType

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.company import Company
    from app.models.document import Document


class CargoStatus(str, enum.Enum):
    """Yuk hayot-tsikli (CONCEPT.md 3-bo'lim).

    Soddalashtirilgan: ba'zi oraliq holatlar status emas, balki assignment'da
    aks etadi (driver_notified, at_pickup, ...).
    """
    NEW = "new"                          # Zavod yaratdi
    DISTRIBUTED = "distributed"          # Carrier'larga taklif yuborildi
    CARRIER_ACCEPTED = "carrier_accepted"  # Carrier qabul qildi
    ASSIGNED_TRUCK = "assigned_truck"    # Mashina biriktirildi
    PICKED_UP = "picked_up"              # Haydovchi oldi
    IN_TRANSIT = "in_transit"            # Yo'lda
    DELIVERED = "delivered"              # Distributor qabul qildi, TTN imzolandi
    COMPLETED = "completed"              # To'lov + yakunlandi
    CANCELLED = "cancelled"
    FAILED = "failed"


class Cargo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cargo"

    factory_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    distributor_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )

    reference_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    weight_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    required_body_type: Mapped[BodyType | None] = mapped_column(Enum(BodyType, name="body_type"))

    origin_address: Mapped[str] = mapped_column(String(512), nullable=False)
    origin_lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    origin_lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    destination_address: Mapped[str] = mapped_column(String(512), nullable=False)
    destination_lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    destination_lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    pickup_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[CargoStatus] = mapped_column(
        Enum(CargoStatus, name="cargo_status"), nullable=False, default=CargoStatus.NEW
    )

    factory: Mapped["Company"] = relationship(
        foreign_keys=[factory_id], back_populates="cargo_as_factory"
    )
    distributor: Mapped["Company"] = relationship(
        foreign_keys=[distributor_id], back_populates="cargo_as_distributor"
    )
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="cargo")
    documents: Mapped[list["Document"]] = relationship(back_populates="cargo")

    @property
    def origin_location(self) -> dict[str, float]:
        return {"lat": float(self.origin_lat), "lng": float(self.origin_lng)}

    @property
    def destination_location(self) -> dict[str, float]:
        return {"lat": float(self.destination_lat), "lng": float(self.destination_lng)}
