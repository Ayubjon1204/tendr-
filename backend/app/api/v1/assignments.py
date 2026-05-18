from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.assignment import Assignment, AssignmentStatus
from app.models.cargo import Cargo, CargoStatus
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
    truck_id: UUID | None = None,
    status_: AssignmentStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Assignment]:
    stmt = select(Assignment)
    if cargo_id:
        stmt = stmt.where(Assignment.cargo_id == cargo_id)
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
    """Qo'lda biriktirish (dispatcher tomonidan)."""
    cargo = await db.get(Cargo, payload.cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    truck = await db.get(Truck, payload.truck_id)
    if not truck or not truck.is_active:
        raise HTTPException(status_code=404, detail="Truck not found or inactive")
    if payload.driver_id:
        driver = await db.get(Driver, payload.driver_id)
        if not driver or driver.carrier_id != truck.carrier_id:
            raise HTTPException(
                status_code=400, detail="Driver must belong to truck's carrier"
            )
    if cargo.status not in (CargoStatus.NEW, CargoStatus.ASSIGNED):
        raise HTTPException(
            status_code=400,
            detail=f"Cargo status {cargo.status.value} cannot be assigned",
        )

    assignment = Assignment(**payload.model_dump())
    db.add(assignment)
    cargo.status = CargoStatus.ASSIGNED

    schedule = TruckSchedule(
        truck_id=truck.id,
        start_at=payload.planned_pickup_at,
        end_at=payload.planned_delivery_at,
        kind=ScheduleKind.ASSIGNMENT,
        assignment_id=assignment.id,
    )
    db.add(schedule)

    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.post("/auto", response_model=AutoAssignResult)
async def trigger_auto_assign(
    payload: AutoAssignRequest, db: DbSession, _user: CurrentUser
) -> AutoAssignResult:
    """Foydalanuvchi qo'lda avto-biriktirish ishga tushiradi (yangi yuk yaratganda
    avtomatik chaqiriladi, lekin shu endpoint orqali ham qayta chaqirish mumkin)."""
    return await auto_assign_cargo(
        db, payload.cargo_id, max_candidates=payload.max_candidates
    )


@router.post("/auto/preview", response_model=AutoAssignResult)
async def preview_auto_assign(
    payload: AutoAssignRequest, db: DbSession, _user: CurrentUser
) -> AutoAssignResult:
    """Dry-run — nomzodlarni ko'rsatadi, lekin biriktirish yaratmaydi."""
    return await auto_assign_cargo(
        db,
        payload.cargo_id,
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

    # Status transitions — truck va cargo statusiga ta'sir
    if new_status:
        await _apply_status_side_effects(db, a, new_status)

    await db.commit()
    await db.refresh(a)
    return a


async def _apply_status_side_effects(
    db, assignment: Assignment, new_status: AssignmentStatus
) -> None:
    truck = await db.get(Truck, assignment.truck_id)
    cargo = await db.get(Cargo, assignment.cargo_id)
    if not truck or not cargo:
        return

    now = datetime.now(tz=timezone.utc)
    if new_status == AssignmentStatus.ACCEPTED:
        truck.status = TruckStatus.LOADING
    elif new_status == AssignmentStatus.IN_PROGRESS:
        truck.status = TruckStatus.BUSY
        cargo.status = CargoStatus.IN_TRANSIT
        if assignment.actual_pickup_at is None:
            assignment.actual_pickup_at = now
    elif new_status == AssignmentStatus.COMPLETED:
        truck.status = TruckStatus.AVAILABLE
        cargo.status = CargoStatus.DELIVERED
        if assignment.actual_delivery_at is None:
            assignment.actual_delivery_at = now
    elif new_status in (AssignmentStatus.REJECTED, AssignmentStatus.CANCELLED):
        truck.status = TruckStatus.AVAILABLE
        if cargo.status == CargoStatus.ASSIGNED:
            cargo.status = CargoStatus.NEW  # Qayta biriktirish uchun ochiq
