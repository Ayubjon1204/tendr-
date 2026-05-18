from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models.company import Company, CompanyKind
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
async def list_companies(
    db: DbSession,
    _user: CurrentUser,
    kind: CompanyKind | None = None,
    is_active: bool | None = None,
    q: str | None = Query(None, description="Nom bo'yicha qidirish"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
) -> list[Company]:
    stmt = select(Company)
    if kind is not None:
        stmt = stmt.where(Company.kind == kind)
    if is_active is not None:
        stmt = stmt.where(Company.is_active.is_(is_active))
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Company.name).offset((page - 1) * size).limit(size)
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate, db: DbSession, _user: CurrentUser
) -> Company:
    company = Company(**payload.model_dump())
    db.add(company)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig))
    await db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: DbSession, _user: CurrentUser) -> Company:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> Company:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID, db: DbSession, _user: CurrentUser) -> None:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.is_active = False
    await db.commit()
