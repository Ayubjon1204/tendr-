from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.assignment import Assignment, AssignmentStatus
from app.models.cargo import Cargo, CargoStatus
from app.models.company import Company, CompanyKind
from app.models.driver import Driver
from app.models.truck import Truck, TruckStatus
from app.models.truck_schedule import ScheduleKind, TruckSchedule
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    AutoAssignRequest,
    AutoAssignResult,
)
from app.services.assignment import auto_assign_cargo

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    db: DbSession,
    _user: CurrentUser,
    cargo_id: UUID | None = None,
    carrier_id: UUID | None = None,
    truck_id: UUID | None = None,
    status_: AssignmentStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Assignment]:
    stmt = select(Assignment)
    if cargo_id:
        stmt = stmt.where(Assignment.cargo_id == cargo_id)
    if carrier_id:
        stmt = stmt.where(Assignment.carrier_id == carrier_id)
    if truck_id:
        stmt = stmt.where(Assignment.truck_id == truck_id)
    if status_:
        stmt = stmt.where(Assignment.status == status_)
    stmt = (
        stmt.order_by(Assignment.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate, db: DbSession, _user: CurrentUser
) -> Assignment:
    cargo = await db.get(Cargo, payload.cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")

    carrier = await db.get(Company, payload.carrier_id)
    if not carrier or carrier.kind != CompanyKind.CARRIER:
        raise HTTPException(
            status_code=400, detail="carrier_id must reference a carrier company"
        )

    if payload.truck_id:
        truck = await db.get(Truck, payload.truck_id)
        if not truck or not truck.is_active:
            raise HTTPException(status_code=404, detail="Truck not found or inactive")
    if payload.driver_id:
        driver = await db.get(Driver, payload.driver_id)
        if not driver:
            raise HTTPException(status_code=400, detail="Driver not found")

    assignment = Assignment(**payload.model_dump())
    db.add(assignment)

    if payload.truck_id:
        cargo.status = CargoStatus.ASSIGNED_TRUCK
        schedule = TruckSchedule(
            truck_id=payload.truck_id,
            start_at=payload.planned_pickup_at,
            end_at=payload.planned_delivery_at,
            kind=ScheduleKind.ASSIGNMENT,
            assignment_id=assignment.id,
        )
        db.add(schedule)
    else:
        cargo.status = CargoStatus.CARRIER_ACCEPTED

    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.post("/auto", response_model=AutoAssignResult)
async def trigger_auto_assign(
    payload: AutoAssignRequest, db: DbSession, _user: CurrentUser
) -> AutoAssignResult:
    return await auto_assign_cargo(
        db, payload.cargo_id, payload.carrier_id, max_candidates=payload.max_candidates
    )


@router.post("/auto/preview", response_model=AutoAssignResult)
async def preview_auto_assign(
    payload: AutoAssignRequest, db: DbSession, _user: CurrentUser
) -> AutoAssignResult:
    return await auto_assign_cargo(
        db,
        payload.cargo_id,
        payload.carrier_id,
        max_candidates=payload.max_candidates,
        create_assignment=False,
    )


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: UUID, db: DbSession, _user: CurrentUser
) -> Assignment:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return a


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Assignment:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    data = payload.model_dump(exclude_unset=True)
    new_status: AssignmentStatus | None = data.get("status")
    for field, value in data.items():
        setattr(a, field, value)

    if new_status:
        await _apply_status_side_effects(db, a, new_status)

    await db.commit()
    await db.refresh(a)
    return a


async def _apply_status_side_effects(
    db, assignment: Assignment, new_status: AssignmentStatus
) -> None:
    cargo = await db.get(Cargo, assignment.cargo_id)
    truck = await db.get(Truck, assignment.truck_id) if assignment.truck_id else None
    if not cargo:
        return

    now = datetime.now(tz=timezone.utc)
    if new_status == AssignmentStatus.ACCEPTED:
        cargo.status = CargoStatus.CARRIER_ACCEPTED
        if truck:
            truck.status = TruckStatus.LOADING
    elif new_status == AssignmentStatus.IN_PROGRESS:
        cargo.status = CargoStatus.IN_TRANSIT
        if truck:
            truck.status = TruckStatus.BUSY
        if assignment.actual_pickup_at is None:
            assignment.actual_pickup_at = now
    elif new_status == AssignmentStatus.COMPLETED:
        cargo.status = CargoStatus.DELIVERED
        if truck:
            truck.status = TruckStatus.AVAILABLE
        if assignment.actual_delivery_at is None:
            assignment.actual_delivery_at = now
    elif new_status in (AssignmentStatus.REJECTED, AssignmentStatus.CANCELLED):
        if truck:
            truck.status = TruckStatus.AVAILABLE
        if cargo.status in (CargoStatus.ASSIGNED_TRUCK, CargoStatus.CARRIER_ACCEPTED):
            cargo.status = CargoStatus.NEW
