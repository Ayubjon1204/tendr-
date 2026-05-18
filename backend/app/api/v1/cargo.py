from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models.cargo import Cargo, CargoStatus
from app.models.company import Company, CompanyKind
from app.schemas.cargo import CargoCreate, CargoOut, CargoUpdate

router = APIRouter(prefix="/cargo", tags=["cargo"])


@router.get("", response_model=list[CargoOut])
async def list_cargo(
    db: DbSession,
    _user: CurrentUser,
    factory_id: UUID | None = None,
    distributor_id: UUID | None = None,
    status_: CargoStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Cargo]:
    stmt = select(Cargo)
    if factory_id:
        stmt = stmt.where(Cargo.factory_id == factory_id)
    if distributor_id:
        stmt = stmt.where(Cargo.distributor_id == distributor_id)
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
) -> Cargo:
    factory = await db.get(Company, payload.factory_id)
    if not factory or factory.kind != CompanyKind.FACTORY:
        raise HTTPException(
            status_code=400, detail="factory_id must reference a factory-type company"
        )
    distributor = await db.get(Company, payload.distributor_id)
    if not distributor or distributor.kind != CompanyKind.DISTRIBUTOR:
        raise HTTPException(
            status_code=400, detail="distributor_id must reference a distributor-type company"
        )

    data = payload.model_dump(exclude={"origin_location", "destination_location"})
    cargo = Cargo(
        **data,
        origin_lat=Decimal(str(payload.origin_location.lat)),
        origin_lng=Decimal(str(payload.origin_location.lng)),
        destination_lat=Decimal(str(payload.destination_location.lat)),
        destination_lng=Decimal(str(payload.destination_location.lng)),
    )
    db.add(cargo)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig))
    await db.refresh(cargo)
    return cargo


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
    if cargo.status in (CargoStatus.DELIVERED, CargoStatus.IN_TRANSIT, CargoStatus.COMPLETED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel cargo with status {cargo.status.value}",
        )
    cargo.status = CargoStatus.CANCELLED
    await db.commit()
