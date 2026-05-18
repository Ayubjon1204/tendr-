import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cargo import Cargo
    from app.models.driver import Driver
    from app.models.truck import Truck


class CompanyKind(str, enum.Enum):
    CARRIER = "carrier"
    SHIPPER = "shipper"


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[CompanyKind] = mapped_column(
        Enum(CompanyKind, name="company_kind"), nullable=False
    )
    tax_id: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trucks: Mapped[list["Truck"]] = relationship(back_populates="carrier")
    drivers: Mapped[list["Driver"]] = relationship(back_populates="carrier")
    cargo: Mapped[list["Cargo"]] = relationship(back_populates="shipper")
