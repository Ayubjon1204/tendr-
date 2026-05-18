import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company


class UserRole(str, enum.Enum):
    """Tashkilot ichida foydalanuvchi roli.

    `owner` — tashkilot egasi, hammasi
    `admin` — boshqaruvchi, foydalanuvchilarni yaratish/o'chirish
    `dispatcher` — kunlik operatsiya (buyurtma, biriktirish, status)
    `accountant` — moliya, hujjatlar
    `viewer` — faqat ko'rish
    """
    OWNER = "owner"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # `company_id is None` => super-admin (platform admin, tendr xodimi)
    company_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="SET NULL")
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.DISPATCHER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company | None"] = relationship(back_populates="users")
