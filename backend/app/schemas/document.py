from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentKind, DocumentStatus


class DocumentBase(BaseModel):
    cargo_id: UUID
    kind: DocumentKind = DocumentKind.TTN


class DocumentCreate(DocumentBase):
    number: str | None = Field(None, max_length=64)


class DocumentSignFactory(BaseModel):
    signature: str  # base64 image yoki URL


class DocumentSignDriverPickup(BaseModel):
    signature: str


class DocumentSignDriverDelivery(BaseModel):
    signature: str


class DocumentSignDistributor(BaseModel):
    signature: str
    actual_weight_kg: int | None = None
    actual_volume_m3: Decimal | None = None
    discrepancy_notes: str | None = None


class DocumentOut(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: DocumentStatus
    number: str | None
    factory_signed_at: datetime | None
    driver_pickup_signed_at: datetime | None
    driver_delivery_signed_at: datetime | None
    distributor_signed_at: datetime | None
    discrepancy_notes: str | None
    actual_weight_kg: int | None
    actual_volume_m3: Decimal | None
    pdf_url: str | None
    qr_code_payload: str | None
    created_at: datetime
    updated_at: datetime
