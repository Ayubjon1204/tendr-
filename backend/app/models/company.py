"""Company = umumiy "Organization" tushunchasi.

Konsepsiyada bu **Organization** deyiladi: tashkilot 4 turdan biri bo'lishi mumkin:
factory (zavod), carrier (transport kompaniya), distributor (mijoz/qabul qiluvchi).

Carrier yana 3 ta sub-tipga bo'linadi (carrier_type):
- hybrid: o'z mashinasi + ekspeditorlik
- forwarder: faqat ekspeditorlik (mashinasiz)
- asset_only: faqat o'z mashinasi
"""
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cargo import Cargo
    from app.models.driver import Driver
    from app.models.truck import Truck
    from app.models.user import User


class CompanyKind(str, enum.Enum):
    FACTORY = "factory"            # Yuk egasi (buyurtma yaratuvchi)
    CARRIER = "carrier"            # Transport kompaniya
    DISTRIBUTOR = "distributor"    # Qabul qiluvchi (mijoz)


class CarrierType(str, enum.Enum):
    HYBRID = "hybrid"            # O'z mashina + ekspeditorlik
    FORWARDER = "forwarder"      # Faqat ekspeditor (mashinasiz)
    ASSET_ONLY = "asset_only"    # Faqat o'z mashinasi


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[CompanyKind] = mapped_column(
        Enum(CompanyKind, name="company_kind"), nullable=False
    )
    carrier_type: Mapped[CarrierType | None] = mapped_column(
        Enum(CarrierType, name="carrier_type")
    )
    tax_id: Mapped[str | None] = mapped_column(String(64))  # STIR
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="company")
    trucks: Mapped[list["Truck"]] = relationship(
        back_populates="carrier", foreign_keys="Truck.carrier_id"
    )
    drivers: Mapped[list["Driver"]] = relationship(back_populates="carrier")
    cargo_as_factory: Mapped[list["Cargo"]] = relationship(
        back_populates="factory", foreign_keys="Cargo.factory_id"
    )
    cargo_as_distributor: Mapped[list["Cargo"]] = relationship(
        back_populates="distributor", foreign_keys="Cargo.distributor_id"
    )
