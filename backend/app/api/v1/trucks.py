from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models.company import Company, CompanyKind
from app.models.location_history import LocationHistory
from app.models.truck import Truck, TruckStatus
from app.schemas.truck import TruckCreate, TruckLocationUpdate, TruckOut, TruckUpdate
from app.services.geo import geopoint_to_wkt

router = APIRouter(prefix="/trucks", tags=["trucks"])


@router.get("", response_model=list[TruckOut])
async def list_trucks(
    db: DbSession,
    _user: CurrentUser,
    carrier_id: UUID | None = None,
    status_: TruckStatus | None = Query(None, alias="status"),
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Truck]:
    stmt = select(Truck)
    if carrier_id:
        stmt = stmt.where(Truck.carrier_id == carrier_id)
    if status_:
        stmt = stmt.where(Truck.status == status_)
    if is_active is not None:
        stmt = stmt.where(Truck.is_active.is_(is_active))
    stmt = stmt.order_by(Truck.plate_number).offset((page - 1) * size).limit(size)
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=TruckOut, status_code=status.HTTP_201_CREATED)
async def create_truck(payload: TruckCreate, db: DbSession, _user: CurrentUser) -> Truck:
    carrier = await db.get(Company, payload.carrier_id)
    if not carrier or carrier.kind != CompanyKind.CARRIER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="carrier_id must reference a carrier-type company",
        )

    data = payload.model_dump(exclude={"current_location", "home_base_location"})
    truck = Truck(**data)
    if payload.current_location:
        truck.current_location = geopoint_to_wkt(payload.current_location)
        truck.last_location_update = datetime.now(tz=timezone.utc)
    if payload.home_base_location:
        truck.home_base_location = geopoint_to_wkt(payload.home_base_location)

    db.add(truck)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig))
    await db.refresh(truck)
    return truck


@router.get("/{truck_id}", response_model=TruckOut)
async def get_truck(truck_id: UUID, db: DbSession, _user: CurrentUser) -> Truck:
    truck = await db.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck


@router.patch("/{truck_id}", response_model=TruckOut)
async def update_truck(
    truck_id: UUID,
    payload: TruckUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Truck:
    truck = await db.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    data = payload.model_dump(exclude_unset=True, exclude={"home_base_location"})
    for field, value in data.items():
        setattr(truck, field, value)
    if "home_base_location" in payload.model_fields_set and payload.home_base_location:
        truck.home_base_location = geopoint_to_wkt(payload.home_base_location)

    await db.commit()
    await db.refresh(truck)
    return truck


@router.post("/{truck_id}/location", response_model=TruckOut)
async def update_truck_location(
    truck_id: UUID,
    payload: TruckLocationUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Truck:
    """Mashina joylashuvini yangilash (mobile app yoki manual)."""
    truck = await db.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    now = datetime.now(tz=timezone.utc)
    truck.current_location = geopoint_to_wkt(payload.location)
    truck.last_location_update = now

    history = LocationHistory(
        truck_id=truck.id,
        location=geopoint_to_wkt(payload.location),
        speed_kmh=payload.speed_kmh,
        heading=payload.heading,
        recorded_at=now,
    )
    db.add(history)
    await db.commit()
    await db.refresh(truck)
    return truck


@router.delete("/{truck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_truck(truck_id: UUID, db: DbSession, _user: CurrentUser) -> None:
    truck = await db.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    truck.is_active = False
    await db.commit()
