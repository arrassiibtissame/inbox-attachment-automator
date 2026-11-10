
import base64
import hashlib
import logging
import re

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config.settings import settings

from backend.database.models.document import DocumentStatus
from backend.database.models.document_receipt import ReceiptSource
from backend.database.models.sync_account import SyncProvider
from backend.database.models.file import File

from backend.database.repositories.file_repository import FileRepository
from backend.database.repositories.document_repository import DocumentRepository
from backend.database.repositories.document_receipt_repository import (
    DocumentReceiptRepository,
)
from backend.database.repositories.document_event_repository import (
    DocumentEventRepository,
)
from backend.database.repositories.sync_account_repository import (
    SyncAccountRepository,
)
from backend.database.repositories.sync_state_repository import (
    SyncStateRepository,
)


logger = logging.getLogger("FIDOMEK_ONE.GMAIL")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TIMEZONE = ZoneInfo(settings.TIMEZONE)

ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS)


class GmailService:
    """Handles Gmail authentication and document synchronization."""

    def __init__(self):
        self.storage_dir = Path(settings.STORAGE_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    def authenticate(self):
        credentials = None
        token_file = settings.GMAIL_TOKEN_FILE
        secret_file = settings.GMAIL_CLIENT_SECRET_FILE

        if token_file.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_file),
                SCOPES,
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if not secret_file.exists():
                raise FileNotFoundError(
                    f"OAuth client secret introuvable : {secret_file}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(secret_file),
                SCOPES,
            )

            credentials = flow.run_local_server(port=0)

            token_file.write_text(
                credentials.to_json(),
                encoding="utf-8",
            )

        service = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

        profile = (
            service.users()
            .getProfile(userId="me")
            .execute()
        )

        email = profile.get("emailAddress")

        if not email:
            raise RuntimeError("Adresse Gmail introuvable.")

        logger.info("Gmail connecté : %s", email)

        return service, profile

    # --------------------------------------------------------
    # GMAIL SEARCH
    # --------------------------------------------------------

    @staticmethod
    def build_query():
        now = datetime.now(TIMEZONE)

        start_date = (now - timedelta(days=2)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        timestamp = int(start_date.timestamp())

        return f"after:{timestamp} has:attachment"

    # --------------------------------------------------------
    # FILE UTILITIES
    # --------------------------------------------------------

    @staticmethod
    def decode_attachment(data: str) -> bytes:
        if not data:
            return b""

        padding = "=" * (-len(data) % 4)

        return base64.urlsafe_b64decode(data + padding)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        filename = Path(filename).name

        filename = re.sub(
            r'[<>:"/\\|?*\x00-\x1f]',
            "_",
            filename,
        )

        filename = filename.strip(" .")

        if not filename:
            filename = "document_sans_nom"

        return filename[:180]

    def validate_file(self, filename: str, content: bytes) -> bool:
        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            logger.warning("Extension non autorisée : %s", filename)
            return False

        if not content:
            logger.warning("Fichier vide : %s", filename)
            return False

        if len(content) > self.max_file_size:
            logger.warning("Fichier trop volumineux : %s", filename)
            return False

        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            logger.warning("Signature PDF invalide : %s", filename)
            return False

        return True

    @staticmethod
    def calculate_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def write_file(self, path: Path, content: bytes):
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = path.with_name(path.name + ".tmp")

        try:
            temporary_path.write_bytes(content)
            temporary_path.replace(path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    # --------------------------------------------------------
    # MESSAGE METADATA
    # --------------------------------------------------------

    @staticmethod
    def get_header(headers: list, name: str) -> str | None:
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value")

        return None

    # --------------------------------------------------------
    # ATTACHMENT EXTRACTION
    # --------------------------------------------------------

    def extract_attachments(self, service, message_id, payload):
        attachments = []

        def walk(parts, parent_key=""):
            for index, part in enumerate(parts):
                part_key = (
                    f"{parent_key}.{index}"
                    if parent_key
                    else str(index)
                )

                filename = part.get("filename", "")

                if filename:
                    body = part.get("body", {})
                    data = body.get("data")

                    if body.get("attachmentId"):
                        attachment = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(
                                userId="me",
                                messageId=message_id,
                                id=body["attachmentId"],
                            )
                            .execute()
                        )

                        data = attachment.get("data")

                    if data:
                        attachments.append({
                            "filename": filename,
                            "part_id": part_key,
                            "mime_type": part.get("mimeType"),
                            "data": data,
                        })

                nested_parts = part.get("parts", [])

                if nested_parts:
                    walk(nested_parts, part_key)

        walk(payload.get("parts", []))

        if payload.get("filename"):
            walk([payload])

        return attachments

    # --------------------------------------------------------
    # DATABASE + STORAGE
    # --------------------------------------------------------

    def save_attachment(
        self,
        session: Session,
        *,
        filename: str,
        content: bytes,
        mime_type: str | None,
        message_id: str,
        part_id: str,
        sender: str | None,
        subject: str | None,
        thread_id: str | None,
        received_at: str | None,
        created_paths: list[Path],
    ) -> bool:
        file_repository = FileRepository(session)
        document_repository = DocumentRepository(session)
        receipt_repository = DocumentReceiptRepository(session)
        event_repository = DocumentEventRepository(session)

        file_hash = self.calculate_hash(content)

        existing_receipt = receipt_repository.get_by_source_message_part(
            source=ReceiptSource.GMAIL,
            source_message_id=message_id,
            source_part_id=part_id,
        )

        stored_file = file_repository.get_by_sha256(file_hash)

        if stored_file:
            destination = Path(stored_file.storage_path)

            try:
                destination.resolve().relative_to(
                    self.storage_dir.resolve()
                )
            except ValueError:
                raise RuntimeError(
                    "Le chemin du fichier existant est hors du stockage autorisé."
                )

            if (
                not destination.is_file()
                or self.calculate_hash(destination.read_bytes()) != file_hash
            ):
                self.write_file(destination, content)

        else:
            if existing_receipt:
                raise RuntimeError(
                    "Reçu Gmail existant, mais fichier correspondant introuvable."
                )

            safe_name = self.sanitize_filename(filename)

            destination = (
                self.storage_dir
                / file_hash[:2]
                / f"{file_hash}_{safe_name}"
            )

            self.write_file(destination, content)
            created_paths.append(destination)

            stored_file = file_repository.create(
                original_filename=safe_name,
                stored_filename=destination.name,
                storage_path=str(destination),
                sha256=file_hash,
                extension=Path(safe_name).suffix.lower(),
                size_bytes=len(content),
                mime_type=mime_type,
            )

        if existing_receipt:
            logger.info(
                "Pièce jointe déjà enregistrée : %s",
                filename,
            )
            return False

        existing_receipts = receipt_repository.list_by_file(
            stored_file.id
        )

        if existing_receipts:
            document = document_repository.get_by_id(
                existing_receipts[0].document_id
            )
        else:
            document = None

        if document is None:
            document = document_repository.create(
                status=DocumentStatus.TO_REVIEW,
            )

            event_repository.create(
                document_id=document.id,
                event_type="DOCUMENT_RECEIVED",
                new_values={
                    "status": DocumentStatus.TO_REVIEW.value,
                    "filename": filename,
                },
                event_metadata={
                    "source": "GMAIL",
                    "message_id": message_id,
                },
            )

        receipt_repository.create(
            document_id=document.id,
            file_id=stored_file.id,
            source=ReceiptSource.GMAIL,
            source_message_id=message_id,
            source_part_id=part_id,
            sender=sender,
            source_metadata={
                "subject": subject,
                "thread_id": thread_id,
                "mime_type": mime_type,
                "received_at": received_at,
            },
        )

        logger.info(
            "Document enregistré : %s (document_id=%s)",
            filename,
            document.id,
        )

        return True

    # --------------------------------------------------------
    # MESSAGE PROCESSING
    # --------------------------------------------------------

    def process_message(
        self,
        service,
        session: Session,
        message_id: str,
    ) -> int:

        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        sender = self.get_header(headers, "From")
        subject = self.get_header(headers, "Subject")

        thread_id = message.get("threadId")
        internal_date = message.get("internalDate")

        received_at = None

        if internal_date:
            received_at = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=timezone.utc,
            ).isoformat()

        attachments = self.extract_attachments(
            service,
            message_id,
            payload,
        )

        created_paths = []
        saved_count = 0

        try:
            with session.begin():
                for attachment in attachments:
                    filename = attachment["filename"]

                    try:
                        content = self.decode_attachment(
                            attachment["data"]
                        )

                        if not self.validate_file(filename, content):
                            continue

                        saved = self.save_attachment(
                            session,
                            filename=filename,
                            content=content,
                            mime_type=attachment["mime_type"],
                            message_id=message_id,
                            part_id=attachment["part_id"],
                            sender=sender,
                            subject=subject,
                            thread_id=thread_id,
                            received_at=received_at,
                            created_paths=created_paths,
                        )

                        if saved:
                            saved_count += 1

                    except Exception:
                        logger.exception(
                            "Erreur sur la pièce jointe : %s",
                            filename,
                        )
                        raise

        except Exception:
            try:
                for path in created_paths:
                    if not path.is_file():
                        continue

                    referenced_file = session.scalar(
                        select(File.id).where(
                            File.storage_path == str(path)
                        )
                    )

                    if referenced_file is None:
                        path.unlink()

            except Exception:
                logger.exception(
                    "Erreur pendant le nettoyage des fichiers après échec."
                )

            finally:
                session.rollback()

            raise

        return saved_count

    # --------------------------------------------------------
    # FULL SYNCHRONIZATION
    # --------------------------------------------------------

    
    def sync_once(self, session: Session) -> dict:
        service, profile = self.authenticate()
    
        email = profile["emailAddress"]
    
        account_repository = SyncAccountRepository(session)
        state_repository = SyncStateRepository(session)
    
        with session.begin():
            account = account_repository.get_by_email(email)
    
            if account is None:
                account = account_repository.create(
                    email=email,
                    provider=SyncProvider.GMAIL,
                )
    
            account_repository.mark_connected(account.id)
    
            state = state_repository.get_by_account_id(account.id)
    
            if state is None:
                state = state_repository.create(
                    sync_account_id=account.id,
                )
    
            state_id = state.id
            state_repository.update_attempt(state_id)
    
        processed_messages = 0
        saved_documents = 0
        failed_messages = []
    
        query = self.build_query()
        page_token = None
    
        logger.info("Début de synchronisation Gmail : %s", email)
    
        try:
            while True:
                response = (
                    service.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        maxResults=100,
                        pageToken=page_token,
                    )
                    .execute()
                )
    
                for message in response.get("messages", []):
                    message_id = message["id"]
    
                    try:
                        saved_documents += self.process_message(
                            service,
                            session,
                            message_id,
                        )
    
                        processed_messages += 1
    
                    except Exception as exc:
                        logger.exception(
                            "Échec du traitement du message Gmail %s",
                            message_id,
                        )
    
                        failed_messages.append({
                            "message_id": message_id,
                            "error": str(exc),
                        })
    
                page_token = response.get("nextPageToken")
    
                if not page_token:
                    break
    
            with session.begin():
                if failed_messages:
                    error_summary = "; ".join(
                        f"{item['message_id']}: {item['error']}"
                        for item in failed_messages
                    )
    
                    state_repository.mark_error(
                        state_id,
                        error=error_summary[:2000],
                    )
                else:
                    state_repository.mark_success(state_id)
    
        except Exception as exc:
            session.rollback()
    
            logger.exception(
                "Erreur pendant la synchronisation Gmail de %s",
                email,
            )
    
            with session.begin():
                state_repository.mark_error(
                    state_id,
                    error=str(exc)[:2000],
                )
    
            raise
    
        logger.info(
            "Synchronisation terminée : %s messages traités, "
            "%s documents enregistrés, %s erreurs.",
            processed_messages,
            saved_documents,
            len(failed_messages),
        )
    
        return {
            "email": email,
            "processed_messages": processed_messages,
            "saved_documents": saved_documents,
            "failed_messages": failed_messages,
        }
