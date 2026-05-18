from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.DISPATCHER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    company_id: UUID | None = None  # None = super-admin


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None
    is_active: bool
    created_at: datetime
