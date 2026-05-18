from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BodyType
from app.models.truck import TruckStatus
from app.schemas.common import GeoPoint, GeoPointOrNone


class TruckBase(BaseModel):
    plate_number: str = Field(..., min_length=1, max_length=32)
    model: str | None = Field(None, max_length=128)
    capacity_kg: int = Field(..., gt=0, le=200_000)
    capacity_volume_m3: Decimal | None = Field(None, gt=0, le=1000)
    body_type: BodyType = BodyType.TENT


class TruckCreate(TruckBase):
    carrier_id: UUID
    current_location: GeoPoint | None = None
    home_base_location: GeoPoint | None = None


class TruckUpdate(BaseModel):
    plate_number: str | None = Field(None, min_length=1, max_length=32)
    model: str | None = Field(None, max_length=128)
    capacity_kg: int | None = Field(None, gt=0, le=200_000)
    capacity_volume_m3: Decimal | None = Field(None, gt=0, le=1000)
    body_type: BodyType | None = None
    status: TruckStatus | None = None
    home_base_location: GeoPoint | None = None
    is_active: bool | None = None


class TruckLocationUpdate(BaseModel):
    location: GeoPoint
    speed_kmh: Decimal | None = Field(None, ge=0, le=200)
    heading: Decimal | None = Field(None, ge=0, lt=360)


class TruckOut(TruckBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    carrier_id: UUID
    status: TruckStatus
    current_location: GeoPointOrNone = None
    home_base_location: GeoPointOrNone = None
    last_location_update: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
