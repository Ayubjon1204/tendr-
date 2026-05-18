from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.db.session import AsyncSessionLocal
from app.models.cargo import Cargo, CargoStatus
from app.models.company import Company, CompanyKind
from app.schemas.cargo import CargoCreate, CargoOut, CargoUpdate
from app.services.assignment import auto_assign_cargo
from app.services.geo import geopoint_to_wkt

router = APIRouter(prefix="/cargo", tags=["cargo"])


@router.get("", response_model=list[CargoOut])
async def list_cargo(
    db: DbSession,
    _user: CurrentUser,
    shipper_id: UUID | None = None,
    status_: CargoStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Cargo]:
    stmt = select(Cargo)
    if shipper_id:
        stmt = stmt.where(Cargo.shipper_id == shipper_id)
    if status_:
        stmt = stmt.where(Cargo.status == status_)
    stmt = (
        stmt.order_by(Cargo.delivery_deadline)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
async def create_cargo(
    payload: CargoCreate,
    db: DbSession,
    _user: CurrentUser,
    background_tasks: BackgroundTasks,
    auto_assign: bool = Query(True, description="Yarating + avto-biriktirish"),
) -> Cargo:
    shipper = await db.get(Company, payload.shipper_id)
    if not shipper or shipper.kind != CompanyKind.SHIPPER:
        raise HTTPException(
            status_code=400, detail="shipper_id must reference a shipper-type company"
        )

    data = payload.model_dump(exclude={"origin_location", "destination_location"})
    cargo = Cargo(
        **data,
        origin_location=geopoint_to_wkt(payload.origin_location),
        destination_location=geopoint_to_wkt(payload.destination_location),
    )
    db.add(cargo)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig))
    await db.refresh(cargo)

    if auto_assign:
        # Background: yangi yuk uchun avto-biriktirish
        background_tasks.add_task(_run_auto_assign, cargo.id)

    return cargo


async def _run_auto_assign(cargo_id: UUID) -> None:
    """BackgroundTasks ichida ishlatish uchun (mustaqil DB session)."""
    async with AsyncSessionLocal() as db:
        await auto_assign_cargo(db, cargo_id, create_assignment=True)


@router.get("/{cargo_id}", response_model=CargoOut)
async def get_cargo(cargo_id: UUID, db: DbSession, _user: CurrentUser) -> Cargo:
    cargo = await db.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    return cargo


@router.patch("/{cargo_id}", response_model=CargoOut)
async def update_cargo(
    cargo_id: UUID,
    payload: CargoUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Cargo:
    cargo = await db.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cargo, field, value)
    await db.commit()
    await db.refresh(cargo)
    return cargo


@router.delete("/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_cargo(cargo_id: UUID, db: DbSession, _user: CurrentUser) -> None:
    cargo = await db.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    if cargo.status in (CargoStatus.DELIVERED, CargoStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel cargo with status {cargo.status.value}",
        )
    cargo.status = CargoStatus.CANCELLED
    await db.commit()
