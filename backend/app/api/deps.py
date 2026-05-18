"""Auth dependency'lari va rolga asoslangan ruxsatlar.

3 darajali ruxsat:
1. Authenticated  - faqat login qilgan
2. Organization kind  - "men carrier yoki factory'man" (qaysi app)
3. Role within org    - dispatcher / admin / owner
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.company import Company, CompanyKind
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exc
        uid = UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user or not user.is_active:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_company(
    user: CurrentUser, db: DbSession
) -> Company:
    """Foydalanuvchi tegishli kompaniyani qaytaradi.

    Agar `company_id` None bo'lsa (super-admin), 403 — bu endpoint org-scope'da.
    """
    if user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires an organization-scoped user",
        )
    company = await db.get(Company, user.company_id)
    if not company or not company.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company inactive")
    return company


CurrentCompany = Annotated[Company, Depends(get_current_company)]


def require_role(*roles: UserRole):
    """Foydalanuvchi rolini tekshirish dep'i."""
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return user
    return checker


def require_kind(*kinds: CompanyKind):
    """Tashkilot turi (factory/carrier/distributor) tekshiruvi."""
    async def checker(company: CurrentCompany) -> Company:
        if company.kind not in kinds:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint is only for {', '.join(k.value for k in kinds)}",
            )
        return company
    return checker


# Tez ishlatish uchun preset'lar
RequireFactory = Annotated[Company, Depends(require_kind(CompanyKind.FACTORY))]
RequireCarrier = Annotated[Company, Depends(require_kind(CompanyKind.CARRIER))]
RequireDistributor = Annotated[Company, Depends(require_kind(CompanyKind.DISTRIBUTOR))]
