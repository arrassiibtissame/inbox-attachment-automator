
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base

if TYPE_CHECKING:
    from backend.database.models.user import User


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    internal_code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        unique=True,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    ice: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    if_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    cnss_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    rc_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    rc_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    patente: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    responsible_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    responsible_user: Mapped["User"] = relationship(
        back_populates="managed_clients",
    )
