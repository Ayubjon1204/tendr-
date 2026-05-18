from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.assignment import AssignmentSource, AssignmentStatus


class AssignmentBase(BaseModel):
    cargo_id: UUID
    truck_id: UUID
    driver_id: UUID | None = None
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    notes: str | None = None


class AssignmentCreate(AssignmentBase):
    assigned_by: AssignmentSource = AssignmentSource.DISPATCHER


class AssignmentUpdate(BaseModel):
    status: AssignmentStatus | None = None
    driver_id: UUID | None = None
    planned_pickup_at: datetime | None = None
    planned_delivery_at: datetime | None = None
    actual_pickup_at: datetime | None = None
    actual_delivery_at: datetime | None = None
    notes: str | None = None


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: AssignmentStatus
    assigned_by: AssignmentSource
    actual_pickup_at: datetime | None = None
    actual_delivery_at: datetime | None = None
    optimization_score: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class AutoAssignRequest(BaseModel):
    cargo_id: UUID
    max_candidates: int = Field(5, ge=1, le=20)


class TruckCandidate(BaseModel):
    truck_id: UUID
    plate_number: str
    score: float
    distance_to_pickup_km: float
    capacity_kg: int
    body_type: str
    reasons: list[str]


class AutoAssignResult(BaseModel):
    cargo_id: UUID
    chosen: TruckCandidate | None = None
    candidates: list[TruckCandidate] = []
    assignment_id: UUID | None = None
    message: str
