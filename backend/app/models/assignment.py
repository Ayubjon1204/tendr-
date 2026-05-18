"""Assignment — yuk va mashina o'rtasidagi biriktirish.

Multi-hop subcontract: bitta yuk uchun assignment'lar zanjir bo'lib ketishi mumkin
(Carrier Type 2 — forwarder — yukni boshqa carrier'ga uzatadi).

Misol:
    Cargo C
    └── Assignment A1 (factory → CarrierType2)  status=FORWARDED, truck=NULL
        └── Assignment A2 (CarrierType2 → CarrierType1)  status=ASSIGNED_TRUCK, truck=T1

`parent_assignment_id` orqali bog'lanadi.
"""
import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cargo import Cargo
    from app.models.company import Company
    from app.models.driver import Driver
    from app.models.truck import Truck
    from app.models.truck_schedule import TruckSchedule


class AssignmentStatus(str, enum.Enum):
    PROPOSED = "proposed"            # Tavsiya qilingan (avto yoki qo'lda)
    ACCEPTED = "accepted"            # Carrier qabul qildi
    FORWARDED = "forwarded"          # Type 2 carrier boshqa carrier'ga uzatdi
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"      # Driver yo'lda
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentSource(str, enum.Enum):
    SYSTEM = "system"
    FACTORY = "factory"              # Zavod qo'lda tanladi
    CARRIER = "carrier"              # Carrier qo'lda tanladi (subcontract)


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignments"
    __table_args__ = (
        Index("ix_assignments_cargo", "cargo_id"),
        Index("ix_assignments_truck_status", "truck_id", "status"),
        Index("ix_assignments_carrier", "carrier_id"),
        Index("ix_assignments_parent", "parent_assignment_id"),
    )

    cargo_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cargo.id", ondelete="CASCADE"), nullable=False
    )

    # Multi-hop: ota assignment (subcontract zanjirida)
    parent_assignment_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("assignments.id", ondelete="CASCADE")
    )

    # Qaysi carrier ushbu hop'da mas'ul
    carrier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )

    # Mashina (faqat oxirgi hop'da to'liq, oraliq hop'da NULL bo'lishi mumkin)
    truck_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("trucks.id", ondelete="RESTRICT")
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("drivers.id", ondelete="SET NULL")
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"),
        nullable=False,
        default=AssignmentStatus.PROPOSED,
    )
    assigned_by: Mapped[AssignmentSource] = mapped_column(
        Enum(AssignmentSource, name="assignment_source"),
        nullable=False,
        default=AssignmentSource.SYSTEM,
    )

    planned_pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_delivery_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Marja: agar subcontract bo'lsa, parent va child o'rtasidagi farq
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    optimization_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    notes: Mapped[str | None] = mapped_column(Text)

    cargo: Mapped["Cargo"] = relationship(back_populates="assignments")
    carrier: Mapped["Company"] = relationship()
    truck: Mapped["Truck | None"] = relationship(back_populates="assignments")
    driver: Mapped["Driver | None"] = relationship()
    parent: Mapped["Assignment | None"] = relationship(
        remote_side="Assignment.id", back_populates="children"
    )
    children: Mapped[list["Assignment"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    schedule_entry: Mapped["TruckSchedule | None"] = relationship(back_populates="assignment")
