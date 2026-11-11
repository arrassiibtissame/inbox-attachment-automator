from __future__ import annotations

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models.document import Document, DocumentStatus
from backend.database.models.document_receipt import DocumentReceipt
from backend.database.models.file import File
from backend.database.models.user import User
from backend.services.client_service import ClientService


class ClientDocumentService:
    """Accès sécurisé aux fichiers reçus pour un client."""

    ALLOWED_CATEGORIES = (
        "Juridique",
        "Fiscalité",
        "Comptabilité",
        "Social",
        "Banque",
        "Non classés",
    )

    def __init__(self, session: Session):
        self.session = session
        self.client_service = ClientService(session)

    def list_client_documents(
        self,
        current_user: User,
        client_id: int,
        *,
        search: str | None = None,
        category: str | None = None,
        status: DocumentStatus | str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Retourne les réceptions de fichiers accessibles pour un client."""

        client = self.client_service.get_client(current_user, client_id)
        if client is None:
            raise PermissionError(
                "Client introuvable ou accès non autorisé."
            )

        if page < 1:
            raise ValueError("Le numéro de page doit être supérieur ou égal à 1.")

        if not 1 <= page_size <= 100:
            raise ValueError("La taille de page doit être comprise entre 1 et 100.")

        if category is not None and category not in self.ALLOWED_CATEGORIES:
            raise ValueError("Catégorie de document invalide.")

        if isinstance(status, str):
            try:
                status = DocumentStatus(status)
            except ValueError as exc:
                raise ValueError("Statut de document invalide.") from exc

        filters = [Document.client_id == client_id]

        if category == "Non classés":
            filters.append(Document.category.is_(None))
        elif category is not None:
            filters.append(Document.category == category)

        if status is not None:
            filters.append(Document.status == status)

        if search and search.strip():
            filters.append(
                File.original_filename.ilike(f"%{search.strip()}%")
            )

        total_statement = (
            select(func.count(DocumentReceipt.id))
            .select_from(DocumentReceipt)
            .join(Document, DocumentReceipt.document_id == Document.id)
            .join(File, DocumentReceipt.file_id == File.id)
            .where(*filters)
        )
        total = self.session.scalar(total_statement) or 0

        statement = (
            select(DocumentReceipt, Document, File, User)
            .join(Document, DocumentReceipt.document_id == Document.id)
            .join(File, DocumentReceipt.file_id == File.id)
            .outerjoin(
                User,
                DocumentReceipt.uploaded_by_user_id == User.id,
            )
            .where(*filters)
            .order_by(
                DocumentReceipt.received_at.desc(),
                DocumentReceipt.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = self.session.execute(statement).all()
        items = []

        for receipt, document, file_record, uploader in rows:
            items.append(
                {
                    "document_id": document.id,
                    "receipt_id": receipt.id,
                    "file_id": file_record.id,
                    "name": file_record.original_filename,
                    "path": file_record.storage_path,
                    "size_bytes": file_record.size_bytes,
                    "mime_type": file_record.mime_type,
                    "extension": file_record.extension,
                    "client": client.company_name,
                    "category": document.category,
                    "type": document.document_type,
                    "document_number": document.document_number,
                    "document_date": document.document_date,
                    "status": document.status.value,
                    "date": receipt.received_at,
                    "source": receipt.source.value,
                    "sender": receipt.sender,
                    "uploaded_by": uploader.full_name if uploader else None,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if total else 0,
        }
