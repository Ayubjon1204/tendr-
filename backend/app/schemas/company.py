from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.company import CompanyKind


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    kind: CompanyKind
    tax_id: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=512)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    tax_id: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
