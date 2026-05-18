"""Document — TTN (Tovar-Transport Hujjati) va boshqa hujjatlar.

Asosiy turi — TTN. Kelajakda: shartnoma, invoice, ishonchnoma, h.k.

TTN hayoti:
1. CREATED — zavod yuk yaratganda draft yaratiladi
2. ISSUED — yuklash boshlandi, QR-kod aktiv
3. PICKED_UP_SIGNED — zavod va haydovchi imzoladi (yuklash chog'ida)
4. DELIVERED_SIGNED — distributor va haydovchi imzoladi (tushirish chog'ida)
5. DISCREPANCY — distributor farq aniqladi (qo'shimcha hujjat shakllantirildi)
"""
import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cargo import Cargo


class DocumentKind(str, enum.Enum):
    TTN = "ttn"                    # Tovar-Transport Hujjati (asosiy)
    DELIVERY_RECEIPT = "delivery_receipt"  # Qabul qog'ozi
    DISCREPANCY_ACT = "discrepancy_act"    # Farq akti
    INVOICE = "invoice"                    # Hisob-faktura
    CONTRACT = "contract"                  # Shartnoma


class DocumentStatus(str, enum.Enum):
    CREATED = "created"            # Draft
    ISSUED = "issued"              # Tasdiqlangan, QR aktiv
    PICKED_UP_SIGNED = "picked_up_signed"  # Yuklash imzosi (factory + driver)
    DELIVERED_SIGNED = "delivered_signed"  # Tushirish imzosi (distributor + driver)
    DISCREPANCY = "discrepancy"            # Farq aniqlandi
    CANCELLED = "cancelled"


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    cargo_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cargo.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[DocumentKind] = mapped_column(
        Enum(DocumentKind, name="document_kind"), nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.CREATED,
    )

    # TTN raqami — qonuniy talab, avto-generatsiya
    number: Mapped[str | None] = mapped_column(String(64), unique=True)

    # Imzolar (URL'lar yoki base64 image)
    factory_signature: Mapped[str | None] = mapped_column(Text)
    factory_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    factory_signed_by_user_id: Mapped[UUID | None] = mapped_column(Uuid)

    driver_pickup_signature: Mapped[str | None] = mapped_column(Text)
    driver_pickup_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    driver_delivery_signature: Mapped[str | None] = mapped_column(Text)
    driver_delivery_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    distributor_signature: Mapped[str | None] = mapped_column(Text)
    distributor_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distributor_signed_by_user_id: Mapped[UUID | None] = mapped_column(Uuid)

    # Farq tafsilotlari (DISCREPANCY status uchun)
    discrepancy_notes: Mapped[str | None] = mapped_column(Text)
    actual_weight_kg: Mapped[int | None] = mapped_column()
    actual_volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    # Yaratuvchi PDF/QR
    pdf_url: Mapped[str | None] = mapped_column(String(512))
    qr_code_payload: Mapped[str | None] = mapped_column(String(512))

    cargo: Mapped["Cargo"] = relationship(back_populates="documents")
