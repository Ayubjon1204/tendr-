from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.company import CarrierType, CompanyKind


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    kind: CompanyKind
    carrier_type: CarrierType | None = None
    tax_id: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=512)

    @model_validator(mode="after")
    def _check_carrier_type(self) -> "CompanyBase":
        if self.kind == CompanyKind.CARRIER and self.carrier_type is None:
            raise ValueError("carrier_type is required when kind is 'carrier'")
        if self.kind != CompanyKind.CARRIER and self.carrier_type is not None:
            raise ValueError("carrier_type can only be set when kind is 'carrier'")
        return self


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    carrier_type: CarrierType | None = None
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
