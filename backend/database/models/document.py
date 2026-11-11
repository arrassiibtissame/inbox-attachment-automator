
from datetime import date, datetime, timezone
from enum import Enum
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy import Date, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class DocumentStatus(str, Enum):
    TO_REVIEW = "TO_REVIEW"
    CLASSIFIED = "CLASSIFIED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    document_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    document_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SQLAlchemyEnum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.TO_REVIEW,
        index=True,
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

    __table_args__ = (
    CheckConstraint(
        "status != 'CLASSIFIED' OR client_id IS NOT NULL",
        name="ck_document_classified_requires_client",
    ),
)

    client = relationship("Client")
