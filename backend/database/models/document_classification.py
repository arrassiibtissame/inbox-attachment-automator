
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    JSON,
    Float,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class ClassificationDecision(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"


class DocumentClassification(Base):
    __tablename__ = "document_classifications"

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_classification_confidence_range",
        ),
        CheckConstraint(
            "(decision = 'PENDING' AND reviewed_at IS NULL AND reviewer_id IS NULL) "
            "OR "
            "(decision != 'PENDING' AND reviewed_at IS NOT NULL AND reviewer_id IS NOT NULL)",
            name="ck_classification_review_consistency",
        ),
    )

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

    proposed_client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    extracted_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    decision: Mapped[ClassificationDecision] = mapped_column(
        SQLAlchemyEnum(
            ClassificationDecision,
            name="classification_decision",
        ),
        nullable=False,
        default=ClassificationDecision.PENDING,
    )

    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    document = relationship("Document")
    proposed_client = relationship("Client")
    reviewer = relationship("User")
