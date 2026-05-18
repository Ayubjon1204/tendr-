from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DriverBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=5, max_length=32)
    license_number: str | None = Field(None, max_length=64)


class DriverCreate(DriverBase):
    carrier_id: UUID
    current_truck_id: UUID | None = None


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, min_length=5, max_length=32)
    license_number: str | None = Field(None, max_length=64)
    current_truck_id: UUID | None = None
    is_active: bool | None = None


class DriverOut(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    carrier_id: UUID
    current_truck_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
