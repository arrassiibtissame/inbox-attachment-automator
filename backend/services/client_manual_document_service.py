from __future__ import annotations

import hashlib
import mimetypes
import re
import uuid
from pathlib import Path

from backend.config.settings import settings
from backend.database.models.document import Document, DocumentStatus
from backend.database.models.document_receipt import ReceiptSource
from backend.database.repositories.document_event_repository import (
    DocumentEventRepository,
)
from backend.database.repositories.document_receipt_repository import (
    DocumentReceiptRepository,
)
from backend.database.repositories.document_repository import DocumentRepository
from backend.database.repositories.file_repository import FileRepository
from backend.services.client_service import ClientService
from backend.services.client_event_service import ClientEventService


class ClientManualDocumentService:
    """Ajout manuel et classement s?curis? des documents d'un client."""

    ALLOWED_CATEGORIES = (
        "Juridique",
        "Fiscalité",
        "Comptabilité",
        "Social",
        "Banque",
        "Non classés",
    )

    def __init__(self, session):
        self.session = session
        self.client_service = ClientService(session)
        self.file_repository = FileRepository(session)
        self.document_repository = DocumentRepository(session)
        self.receipt_repository = DocumentReceiptRepository(session)
        self.event_repository = DocumentEventRepository(session)
        self.client_event_service = ClientEventService(session)
        self.storage_dir = Path(settings.STORAGE_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = {
            extension.lower() for extension in settings.ALLOWED_EXTENSIONS
        }

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        filename = Path(filename).name
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
        filename = filename.strip(" .")
        if not filename:
            filename = "document_sans_nom"
        return filename[:180]

    @classmethod
    def _normalize_category(cls, category: str | None) -> str | None:
        if category in (None, "", "Non classés"):
            return None
        if category not in cls.ALLOWED_CATEGORIES:
            raise ValueError("Cat?gorie de document invalide.")
        return category

    def _verify_client(self, current_user, client_id: int):
        client = self.client_service.get_client(current_user, client_id)
        if client is None:
            raise PermissionError(
                "Client introuvable ou acc?s non autoris?."
            )
        return client

    def _validate_file(self, filename: str, content: bytes) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in self.allowed_extensions:
            raise ValueError("Format de fichier non autoris?.")

        if not isinstance(content, bytes) or not content:
            raise ValueError("Le fichier est vide ou invalide.")

        if len(content) > self.max_file_size:
            raise ValueError("Le fichier d?passe la limite de 25 Mo.")

        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise ValueError("Le contenu du fichier PDF est invalide.")

        return extension

    def _resolve_existing_file(self, file_record, file_hash: str) -> Path:
        path = Path(file_record.storage_path)

        try:
            path.resolve().relative_to(self.storage_dir.resolve())
        except ValueError as exc:
            raise RuntimeError(
                "Le fichier existant se trouve hors du stockage autoris?."
            ) from exc

        if not path.is_file():
            raise RuntimeError(
                "Le fichier existe en base, mais il est absent du stockage."
            )

        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != file_hash:
            raise RuntimeError(
                "Le fichier existant ne correspond plus ? son empreinte."
            )

        return path

    def add_manual_document(
        self,
        current_user,
        client_id: int,
        *,
        filename: str,
        content: bytes,
        category: str | None = None,
        mime_type: str | None = None,
    ) -> Document:
        """Ajoute un document au client sans ?craser un fichier existant."""

        client = self._verify_client(current_user, client_id)
        category = self._normalize_category(category)

        safe_name = self._sanitize_filename(filename)
        extension = self._validate_file(safe_name, content)
        file_hash = hashlib.sha256(content).hexdigest()

        existing_file = self.file_repository.get_by_sha256(file_hash)

        if existing_file:
            existing_receipts = self.receipt_repository.list_by_file(
                existing_file.id
            )

            for receipt in existing_receipts:
                existing_document = self.document_repository.get_by_id(
                    receipt.document_id
                )
                if (
                    existing_document
                    and existing_document.client_id == client.id
                ):
                    raise ValueError(
                        "Ce fichier est d?j? associ? ? ce client."
                    )

            destination = self._resolve_existing_file(
                existing_file,
                file_hash,
            )
            file_record = existing_file
            created_path = None

        else:
            destination_dir = self.storage_dir / file_hash[:2]
            destination_dir.mkdir(parents=True, exist_ok=True)

            destination = destination_dir / f"{file_hash}_{safe_name}"

            if destination.exists():
                if (
                    destination.is_file()
                    and hashlib.sha256(destination.read_bytes()).hexdigest()
                    == file_hash
                ):
                    pass
                else:
                    destination = destination_dir / (
                        f"{file_hash}_{uuid.uuid4().hex}_{safe_name}"
                    )

            created_path = None
            try:
                with destination.open("xb") as stream:
                    stream.write(content)
                created_path = destination

                detected_mime = (
                    mime_type
                    or mimetypes.guess_type(safe_name)[0]
                    or "application/octet-stream"
                )

                file_record = self.file_repository.create(
                    original_filename=safe_name,
                    stored_filename=destination.name,
                    storage_path=str(destination),
                    sha256=file_hash,
                    extension=extension,
                    size_bytes=len(content),
                    mime_type=detected_mime,
                )
            except Exception:
                if created_path and created_path.exists():
                    created_path.unlink()
                raise

        try:
            document = self.document_repository.create(
                client_id=client.id,
                category=category,
                status=DocumentStatus.TO_REVIEW,
            )

            self.receipt_repository.create(
                document_id=document.id,
                file_id=file_record.id,
                source=ReceiptSource.MANUAL,
                uploaded_by_user_id=current_user.id,
                sender=current_user.email,
                source_metadata={
                    "original_filename": safe_name,
                    "mime_type": file_record.mime_type,
                },
            )

            self.event_repository.create(
                document_id=document.id,
                event_type="DOCUMENT_MANUALLY_ADDED",
                actor_user_id=current_user.id,
                new_values={
                    "filename": safe_name,
                    "category": category,
                    "source": ReceiptSource.MANUAL.value,
                },
            )

            self.client_event_service.create_event(
                current_user,
                client.id,
                "DOCUMENT_MANUALLY_ADDED",
                new_values={
                    "filename": safe_name,
                    "category": category,
                    "document_id": document.id,
                },
                event_metadata={
                    "source": ReceiptSource.MANUAL.value,
                },
            )

            return document

        except Exception:
            if created_path and created_path.exists():
                created_path.unlink()
            raise

    def update_document_category(
        self,
        current_user,
        client_id: int,
        document_id: int,
        category: str | None,
    ) -> Document:
        """Modifie la cat?gorie d'un document appartenant au client."""

        client = self._verify_client(current_user, client_id)
        category = self._normalize_category(category)

        document = self.document_repository.get_by_id(document_id)

        if document is None or document.client_id != client.id:
            raise PermissionError(
                "Document introuvable ou acc?s non autoris?."
            )

        old_category = document.category
        if old_category == category:
            return document

        document.category = category
        self.session.flush()

        self.event_repository.create(
            document_id=document.id,
            event_type="DOCUMENT_CATEGORY_CHANGED",
            actor_user_id=current_user.id,
            old_values={"category": old_category},
            new_values={"category": category},
        )

        self.client_event_service.create_event(
            current_user,
            client.id,
            "DOCUMENT_CATEGORY_CHANGED",
            old_values={"category": old_category},
            new_values={"category": category},
            event_metadata={
                "document_id": document.id,
            },
        )

        return document
