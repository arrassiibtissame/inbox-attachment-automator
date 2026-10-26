import base64
import hashlib
import logging
import mimetypes
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token_cabinet.json"
DATABASE_FILE = BASE_DIR / "downloads.db"

DOWNLOAD_DIR = Path.home() / "Documents" / "Cabinet-Documents-Test"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TIMEZONE = ZoneInfo("Africa/Casablanca")

# Reste en mode test : seuls les sujets de test sont traités.
TEST_MODE = True

TEST_SUBJECTS = [
    "FIDOMEK_TEST",
    "FIDOMEK_TEST_MULTI",
    "FIDOMEK_TEST_NEW",
]

CHECK_INTERVAL_SECONDS = 300
MAX_FILE_SIZE = 25 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("FIDOMEK_ONE")
# ============================================================
# BASE DE DONNÉES
# ============================================================

def initialize_database():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                message_id TEXT NOT NULL,
                part_key TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                saved_path TEXT NOT NULL,
                downloaded_at TEXT NOT NULL,
                PRIMARY KEY (message_id, part_key)
            )
            """
        )
        connection.commit()


def was_downloaded(message_id, part_key):
    with sqlite3.connect(DATABASE_FILE) as connection:
        cursor = connection.execute(
            """
            SELECT saved_path
            FROM downloads
            WHERE message_id = ? AND part_key = ?
            """,
            (message_id, part_key),
        )
        row = cursor.fetchone()

    if row and row[0] and Path(row[0]).exists():
        return True

    return False


def register_download(message_id, part_key, filename, file_hash, saved_path):
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO downloads (
                message_id,
                part_key,
                filename,
                file_hash,
                saved_path,
                downloaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                part_key,
                filename,
                file_hash,
                str(saved_path),
                datetime.now(TIMEZONE).isoformat(),
            ),
        )
        connection.commit()
        # ============================================================
# AUTHENTIFICATION GMAIL
# ============================================================

def authenticate_gmail():
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Fichier OAuth introuvable : {CLIENT_SECRET_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            SCOPES,
        )

        credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    service = build("gmail", "v1", credentials=credentials)

    profile = service.users().getProfile(userId="me").execute()
    logger.info(
        "Compte Gmail utilisé : %s",
        profile.get("emailAddress"),
    )
    logger.info("Authentification Gmail réussie.")

    return service

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Fichier OAuth introuvable : {CLIENT_SECRET_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            SCOPES,
        )

        credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    service = build("gmail", "v1", credentials=credentials)
    logger.info("Authentification Gmail réussie.")
    return service


# ============================================================
# RECHERCHE DES E-MAILS DU JOUR
# ============================================================

def build_gmail_query():
    now = datetime.now(TIMEZONE)

    start_of_day = now.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_of_day = start_of_day + timedelta(days=1)

    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(end_of_day.timestamp())

    query = (
        f"after:{start_timestamp} "
        f"before:{end_timestamp} "
        "in:inbox has:attachment"
    )

    if TEST_MODE:
        subject_query = " ".join(
            f"subject:{subject}" for subject in TEST_SUBJECTS
        )
        query += f" {{{subject_query}}}"

    logger.info("Recherche Gmail : %s", query)
    return query
# ============================================================
# OUTILS DE TRAITEMENT DES FICHIERS
# ============================================================

def decode_attachment(data):
    """Décode le contenu d'une pièce jointe Gmail."""
    if not data:
        return b""

    return base64.urlsafe_b64decode(data.encode("utf-8"))


def sanitize_filename(filename):
    """Nettoie le nom de fichier pour Windows."""
    filename = Path(filename).name
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    filename = filename.strip(" .")

    if not filename:
        filename = "document_sans_nom"

    return filename[:180]


def unique_file_path(directory, filename, unique_prefix):
    """Évite d'écraser un fichier existant."""
    safe_name = sanitize_filename(filename)
    path = directory / safe_name

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    path = directory / f"{stem}_{unique_prefix}{suffix}"

    counter = 1
    while path.exists():
        path = directory / f"{stem}_{unique_prefix}_{counter}{suffix}"
        counter += 1

    return path


def is_valid_file(filename, content):
    """Vérifications simples avant l'enregistrement."""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        logger.warning("Extension non autorisée : %s", filename)
        return False

    if not content:
        logger.warning("Fichier vide rejeté : %s", filename)
        return False

    if len(content) > MAX_FILE_SIZE:
        logger.warning("Fichier trop volumineux : %s", filename)
        return False

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        logger.warning("Signature PDF invalide : %s", filename)
        return False

    return True
# ============================================================
# TRAITEMENT DES PIÈCES JOINTES
# ============================================================

def process_message(service, message_id):
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = next(
        (
            header.get("value", "")
            for header in headers
            if header.get("name", "").lower() == "subject"
        ),
        "(sans sujet)",
    )

    logger.info("Traitement du message : %s", subject)

    def process_parts(parts, parent_key=""):
        for index, part in enumerate(parts):
            part_key = f"{parent_key}.{index}" if parent_key else str(index)
            filename = part.get("filename", "")

            if filename:
                body = part.get("body", {})
                attachment_id = body.get("attachmentId")
                data = body.get("data")

                if attachment_id:
                    attachment = (
                        service.users()
                        .messages()
                        .attachments()
                        .get(
                            userId="me",
                            messageId=message_id,
                            id=attachment_id,
                        )
                        .execute()
                    )
                    data = attachment.get("data")

                if data:
                    try:
                        content = decode_attachment(data)
                    except Exception:
                        logger.exception(
                            "Impossible de décoder la pièce jointe : %s",
                            filename,
                        )
                        content = None

                    if content is not None and is_valid_file(filename, content):
                        if was_downloaded(message_id, part_key):
                            logger.info("Déjà téléchargé : %s", filename)
                        else:
                            file_hash = hashlib.sha256(content).hexdigest()
                            unique_prefix = hashlib.sha256(
                                f"{message_id}:{part_key}".encode("utf-8")
                            ).hexdigest()[:8]

                            destination = unique_file_path(
                                DOWNLOAD_DIR,
                                filename,
                                unique_prefix,
                            )

                            try:
                                destination.write_bytes(content)
                                register_download(
                                    message_id,
                                    part_key,
                                    sanitize_filename(filename),
                                    file_hash,
                                    destination,
                                )
                                logger.info(
                                    "Téléchargé : %s",
                                    destination.name,
                                )
                            except OSError:
                                logger.exception(
                                    "Erreur d'enregistrement : %s",
                                    filename,
                                )

            nested_parts = part.get("parts", [])
            if nested_parts:
                process_parts(nested_parts, part_key)

    process_parts(payload.get("parts", []))

    # Certains e-mails contiennent une seule pièce jointe directement.
    if payload.get("filename"):
        process_parts([payload])
    # ============================================================
# VÉRIFICATION PÉRIODIQUE
# ============================================================

def check_emails(service):
    query = build_gmail_query()
    page_token = None
    processed_count = 0

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

        messages = response.get("messages", [])

        for message in messages:
            try:
                process_message(service, message["id"])
                processed_count += 1
            except HttpError:
                logger.exception(
                    "Erreur Gmail pour le message %s",
                    message.get("id"),
                )
            except Exception:
                logger.exception(
                    "Erreur inattendue pour le message %s",
                    message.get("id"),
                )

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    logger.info(
        "Vérification terminée. Messages traités : %s",
        processed_count,
    )


# ============================================================
# POINT D'ENTRÉE
# ============================================================

def main():
    logger.info("FIDOMEK ONE démarre.")
    logger.info("Mode test : %s", TEST_MODE)
    logger.info("Dossier de destination : %s", DOWNLOAD_DIR)
    logger.info("Base de données : %s", DATABASE_FILE)

    initialize_database()
    service = authenticate_gmail()
  

    while True:
        try:
            check_emails(service)
        except HttpError:
            logger.exception("Erreur lors de la vérification Gmail.")
        except Exception:
            logger.exception("Erreur inattendue pendant la vérification.")

        logger.info(
            "Prochaine vérification dans %s secondes.",
            CHECK_INTERVAL_SECONDS,
        )
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()