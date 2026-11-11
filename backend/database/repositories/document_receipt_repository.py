
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.document_receipt import (
    DocumentReceipt,
    ReceiptSource,
)


class DocumentReceiptRepository:
    """Handles database operations related to document receipts."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        document_id: int,
        file_id: int,
        source: ReceiptSource,
        source_message_id: str | None = None,
        source_part_id: str | None = None,
        sender: str | None = None,
        source_metadata: dict | None = None,
        uploaded_by_user_id: int | None = None,
    ) -> DocumentReceipt:
        receipt = DocumentReceipt(
            document_id=document_id,
            file_id=file_id,
            source=source,
            source_message_id=source_message_id,
            source_part_id=source_part_id,
            sender=sender,
            source_metadata=source_metadata,
            uploaded_by_user_id=uploaded_by_user_id,
        )

        self.session.add(receipt)
        self.session.flush()

        return receipt

    def get_by_id(self, receipt_id: int) -> DocumentReceipt | None:
        return self.session.get(DocumentReceipt, receipt_id)

    def get_by_source_message_part(
        self,
        *,
        source: ReceiptSource,
        source_message_id: str,
        source_part_id: str,
    ) -> DocumentReceipt | None:
        statement = select(DocumentReceipt).where(
            DocumentReceipt.source == source,
            DocumentReceipt.source_message_id == source_message_id,
            DocumentReceipt.source_part_id == source_part_id,
        )

        return self.session.scalars(statement).one_or_none()

    def list_by_document(
        self,
        document_id: int,
    ) -> list[DocumentReceipt]:
        statement = (
            select(DocumentReceipt)
            .where(DocumentReceipt.document_id == document_id)
            .order_by(DocumentReceipt.received_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_by_file(
        self,
        file_id: int,
    ) -> list[DocumentReceipt]:
        statement = (
            select(DocumentReceipt)
            .where(DocumentReceipt.file_id == file_id)
            .order_by(DocumentReceipt.received_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_by_source(
        self,
        source: ReceiptSource,
    ) -> list[DocumentReceipt]:
        statement = (
            select(DocumentReceipt)
            .where(DocumentReceipt.source == source)
            .order_by(DocumentReceipt.received_at.desc())
        )

        return list(self.session.scalars(statement).all())
