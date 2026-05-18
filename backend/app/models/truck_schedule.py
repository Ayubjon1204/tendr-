import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.truck import Truck


class ScheduleKind(str, enum.Enum):
    WORK = "work"
    DAY_OFF = "day_off"
    MAINTENANCE = "maintenance"
    ASSIGNMENT = "assignment"


class TruckSchedule(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "truck_schedule"
    __table_args__ = (
        Index("ix_truck_schedule_truck_window", "truck_id", "start_at", "end_at"),
    )

    truck_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("trucks.id", ondelete="CASCADE"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[ScheduleKind] = mapped_column(
        Enum(ScheduleKind, name="schedule_kind"), nullable=False
    )
    assignment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    truck: Mapped["Truck"] = relationship(back_populates="schedules")
    assignment: Mapped["Assignment | None"] = relationship(back_populates="schedule_entry")
