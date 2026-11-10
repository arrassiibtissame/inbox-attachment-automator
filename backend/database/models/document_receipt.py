
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base
from sqlalchemy import UniqueConstraint

class ReceiptSource(str, Enum):
    GMAIL = "GMAIL"
    WHATSAPP = "WHATSAPP"
    MANUAL = "MANUAL"


class DocumentReceipt(Base):
    __tablename__ = "document_receipts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    source: Mapped[ReceiptSource] = mapped_column(
        SQLAlchemyEnum(ReceiptSource, name="receipt_source"),
        nullable=False,
    )

    source_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_part_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    source_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    __table_args__ = (
    UniqueConstraint(
        "source",
        "source_message_id",
        "source_part_id",
        name="uq_receipt_source_message_part",
    ),
)

    document = relationship("Document")
    file = relationship("File")
