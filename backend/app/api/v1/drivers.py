from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.company import Company, CompanyKind
from app.models.driver import Driver
from app.models.truck import Truck
from app.schemas.driver import DriverCreate, DriverOut, DriverUpdate

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverOut])
async def list_drivers(
    db: DbSession,
    _user: CurrentUser,
    carrier_id: UUID | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Driver]:
    stmt = select(Driver)
    if carrier_id:
        stmt = stmt.where(Driver.carrier_id == carrier_id)
    if is_active is not None:
        stmt = stmt.where(Driver.is_active.is_(is_active))
    stmt = stmt.order_by(Driver.full_name).offset((page - 1) * size).limit(size)
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate, db: DbSession, _user: CurrentUser
) -> Driver:
    carrier = await db.get(Company, payload.carrier_id)
    if not carrier or carrier.kind != CompanyKind.CARRIER:
        raise HTTPException(
            status_code=400, detail="carrier_id must reference a carrier-type company"
        )
    if payload.current_truck_id:
        truck = await db.get(Truck, payload.current_truck_id)
        if not truck or truck.carrier_id != payload.carrier_id:
            raise HTTPException(
                status_code=400, detail="current_truck_id must belong to the same carrier"
            )

    driver = Driver(**payload.model_dump())
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverOut)
async def get_driver(driver_id: UUID, db: DbSession, _user: CurrentUser) -> Driver:
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.patch("/{driver_id}", response_model=DriverOut)
async def update_driver(
    driver_id: UUID,
    payload: DriverUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Driver:
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    await db.commit()
    await db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: UUID, db: DbSession, _user: CurrentUser) -> None:
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.is_active = False
    await db.commit()
