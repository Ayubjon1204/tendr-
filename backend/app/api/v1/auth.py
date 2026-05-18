from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.company import CompanyOut
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == form_data.username.lower()))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    claims = {"role": user.role.value}
    if user.company_id:
        company = await db.get(Company, user.company_id)
        if company:
            claims["company_id"] = str(company.id)
            claims["company_kind"] = company.kind.value
            if company.carrier_type:
                claims["carrier_type"] = company.carrier_type.value

    token = create_access_token(subject=str(user.id), extra_claims=claims)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user


@router.get("/me/company", response_model=CompanyOut | None)
async def me_company(user: CurrentUser, db: DbSession) -> Company | None:
    """Foydalanuvchi tegishli kompaniyani qaytaradi (super-admin uchun None)."""
    if user.company_id is None:
        return None
    return await db.get(Company, user.company_id)
