
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.document_classification import (
    ClassificationDecision,
    DocumentClassification,
)


class DocumentClassificationRepository:
    """Handles database operations related to document classifications."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        document_id: int,
        proposed_client_id: int | None = None,
        confidence: float | None = None,
        extracted_data: dict | None = None,
        rationale: str | None = None,
    ) -> DocumentClassification:
        classification = DocumentClassification(
            document_id=document_id,
            proposed_client_id=proposed_client_id,
            confidence=confidence,
            extracted_data=extracted_data,
            rationale=rationale,
            decision=ClassificationDecision.PENDING,
        )

        self.session.add(classification)
        self.session.flush()

        return classification

    def get_by_id(
        self,
        classification_id: int,
    ) -> DocumentClassification | None:
        return self.session.get(DocumentClassification, classification_id)

    def list_by_document(
        self,
        document_id: int,
    ) -> list[DocumentClassification]:
        statement = (
            select(DocumentClassification)
            .where(DocumentClassification.document_id == document_id)
            .order_by(DocumentClassification.created_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_pending(self) -> list[DocumentClassification]:
        statement = (
            select(DocumentClassification)
            .where(
                DocumentClassification.decision
                == ClassificationDecision.PENDING
            )
            .order_by(DocumentClassification.created_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_by_decision(
        self,
        decision: ClassificationDecision,
    ) -> list[DocumentClassification]:
        statement = (
            select(DocumentClassification)
            .where(DocumentClassification.decision == decision)
            .order_by(DocumentClassification.created_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def record_decision(
        self,
        *,
        classification_id: int,
        decision: ClassificationDecision,
        reviewer_id: int,
    ) -> DocumentClassification | None:
        if decision == ClassificationDecision.PENDING:
            raise ValueError("A review decision cannot be PENDING.")

        classification = self.get_by_id(classification_id)

        if classification is None:
            return None

        if classification.decision != ClassificationDecision.PENDING:
            raise ValueError("This classification has already been reviewed.")

        classification.decision = decision
        classification.reviewer_id = reviewer_id
        classification.reviewed_at = datetime.now(timezone.utc)

        self.session.flush()

        return classification
