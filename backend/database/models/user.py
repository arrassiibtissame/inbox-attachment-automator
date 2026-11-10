from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.database.models.client import Client

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    civility: Mapped[str | None] = mapped_column(
    String(10),
    nullable=True,
)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.EMPLOYEE,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    managed_clients: Mapped[list["Client"]] = relationship(
        back_populates="responsible_user"
    )