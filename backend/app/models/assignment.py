import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cargo import Cargo
    from app.models.driver import Driver
    from app.models.truck import Truck
    from app.models.truck_schedule import TruckSchedule


class AssignmentStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentSource(str, enum.Enum):
    SYSTEM = "system"
    DISPATCHER = "dispatcher"


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignments"
    __table_args__ = (
        Index(
            "ix_assignments_active_cargo_unique",
            "cargo_id",
            unique=True,
            postgresql_where=text("status IN ('proposed','accepted','in_progress')"),
        ),
        Index("ix_assignments_truck_status", "truck_id", "status"),
    )

    cargo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cargo.id", ondelete="CASCADE"), nullable=False
    )
    truck_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("trucks.id", ondelete="RESTRICT"), nullable=False
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL")
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

    optimization_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    notes: Mapped[str | None] = mapped_column(Text)

    cargo: Mapped["Cargo"] = relationship(back_populates="assignments")
    truck: Mapped["Truck"] = relationship(back_populates="assignments")
    driver: Mapped["Driver | None"] = relationship()
    schedule_entry: Mapped["TruckSchedule | None"] = relationship(back_populates="assignment")
