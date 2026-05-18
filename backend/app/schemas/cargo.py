from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.cargo import CargoStatus
from app.models.enums import BodyType
from app.schemas.common import GeoPoint, GeoPointReq


class CargoBase(BaseModel):
    reference_code: str = Field(..., min_length=1, max_length=64)
    description: str | None = None

    weight_kg: int = Field(..., gt=0, le=200_000)
    volume_m3: Decimal | None = Field(None, gt=0, le=1000)
    required_body_type: BodyType | None = None

    origin_address: str = Field(..., min_length=1, max_length=512)
    destination_address: str = Field(..., min_length=1, max_length=512)

    pickup_window_start: datetime
    pickup_window_end: datetime
    delivery_deadline: datetime

    price: Decimal | None = Field(None, ge=0)


class CargoCreate(CargoBase):
    shipper_id: UUID
    origin_location: GeoPoint
    destination_location: GeoPoint

    @model_validator(mode="after")
    def _check_windows(self) -> "CargoCreate":
        if self.pickup_window_end <= self.pickup_window_start:
            raise ValueError("pickup_window_end must be after pickup_window_start")
        if self.delivery_deadline <= self.pickup_window_start:
            raise ValueError("delivery_deadline must be after pickup_window_start")
        return self


class CargoUpdate(BaseModel):
    description: str | None = None
    weight_kg: int | None = Field(None, gt=0, le=200_000)
    volume_m3: Decimal | None = Field(None, gt=0, le=1000)
    required_body_type: BodyType | None = None
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    delivery_deadline: datetime | None = None
    price: Decimal | None = Field(None, ge=0)
    status: CargoStatus | None = None


class CargoOut(CargoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipper_id: UUID
    status: CargoStatus
    origin_location: GeoPointReq
    destination_location: GeoPointReq
    created_at: datetime
    updated_at: datetime
