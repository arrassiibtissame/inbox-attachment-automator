
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.client import Client
from backend.database.models.document import Document, DocumentStatus


class DocumentRepository:
    """Handles database operations related to documents."""

    ALLOWED_CATEGORIES = (
        "Juridique",
        "Fiscalit\u00e9",
        "Comptabilit\u00e9",
        "Social",
        "Banque",
    )

    @classmethod
    def _validate_category(cls, category: str | None) -> None:
        if category is not None and category not in cls.ALLOWED_CATEGORIES:
            raise ValueError("Cat\u00e9gorie de document invalide.")


    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        client_id: int | None = None,
        document_type: str | None = None,
        category: str | None = None,
        document_number: str | None = None,
        document_date: date | None = None,
        status: DocumentStatus = DocumentStatus.TO_REVIEW,
    ) -> Document:
        self._validate_category(category)

        document = Document(
            client_id=client_id,
            document_type=document_type,
            category=category,
            document_number=document_number,
            document_date=document_date,
            status=status,
        )

        self.session.add(document)
        self.session.flush()

        return document

    def get_by_id(self, document_id: int) -> Document | None:
        return self.session.get(Document, document_id)

    def list_all(
        self,
        *,
        status: DocumentStatus | None = None,
    ) -> list[Document]:
        statement = select(Document)

        if status is not None:
            statement = statement.where(Document.status == status)

        statement = statement.order_by(Document.created_at.desc())

        return list(self.session.scalars(statement).all())

    def list_by_client(
        self,
        client_id: int,
        *,
        status: DocumentStatus | None = None,
        category: str | None = None,
    ) -> list[Document]:
        self._validate_category(category)

        statement = select(Document).where(
            Document.client_id == client_id
        )

        if status is not None:
            statement = statement.where(Document.status == status)

        if category is not None:
            statement = statement.where(Document.category == category)

        statement = statement.order_by(Document.created_at.desc())

        return list(self.session.scalars(statement).all())

    def list_by_responsible_user(
        self,
        user_id: int,
        *,
        status: DocumentStatus | None = None,
    ) -> list[Document]:
        statement = (
            select(Document)
            .join(Client, Document.client_id == Client.id)
            .where(Client.responsible_user_id == user_id)
        )

        if status is not None:
            statement = statement.where(Document.status == status)

        statement = statement.order_by(Document.created_at.desc())

        return list(self.session.scalars(statement).all())

    def list_unassigned(self) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.client_id.is_(None),
                Document.status == DocumentStatus.TO_REVIEW,
            )
            .order_by(Document.created_at.desc())
        )

        return list(self.session.scalars(statement).all())
