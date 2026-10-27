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
from contextlib import closing

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

# Reste en mode test : seuls les sujets de test sont traitÃ©s.
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
# BASE DE DONNÃ‰ES
# ============================================================

def initialize_database():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        with connection:
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


def was_downloaded(message_id, part_key):
    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        cursor = connection.execute(
            """
            SELECT saved_path, file_hash
            FROM downloads
            WHERE message_id = ? AND part_key = ?
            """,
            (message_id, part_key),
        )
        row = cursor.fetchone()

    if not row or not row[0] or not row[1]:
        return False

    saved_path = Path(row[0])

    if not saved_path.is_file():
        return False

    try:
        current_hash = hashlib.sha256(saved_path.read_bytes()).hexdigest()
    except OSError:
        return False

    return current_hash == row[1]


def get_registered_download(message_id, part_key):
    """Retourne le chemin et le hash du fichier associÃ© Ã  la piÃ¨ce jointe."""
    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        cursor = connection.execute(
            """
            SELECT saved_path, file_hash
            FROM downloads
            WHERE message_id = ? AND part_key = ?
            """,
            (message_id, part_key),
        )
        row = cursor.fetchone()

    if not row or not row[0] or not row[1]:
        return None

    return Path(row[0]), row[1]



def register_download(message_id, part_key, filename, file_hash, saved_path):
    """CrÃ©e ou actualise l'historique d'une piÃ¨ce jointe tÃ©lÃ©chargÃ©e."""

    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        connection.execute(
            """
            INSERT INTO downloads (
                message_id,
                part_key,
                filename,
                file_hash,
                saved_path,
                downloaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(message_id, part_key) DO UPDATE SET
                filename = excluded.filename,
                file_hash = excluded.file_hash,
                saved_path = excluded.saved_path,
                downloaded_at = excluded.downloaded_at
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
        "Compte Gmail utilisÃ© : %s",
        profile.get("emailAddress"),
    )
    logger.info("Authentification Gmail rÃ©ussie.")

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
    """DÃ©code le contenu d'une piÃ¨ce jointe Gmail."""
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
    """Ã‰vite d'Ã©craser un fichier existant."""
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
    """VÃ©rifications simples avant l'enregistrement."""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        logger.warning("Extension non autorisÃ©e : %s", filename)
        return False

    if not content:
        logger.warning("Fichier vide rejetÃ© : %s", filename)
        return False

    if len(content) > MAX_FILE_SIZE:
        logger.warning("Fichier trop volumineux : %s", filename)
        return False

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        logger.warning("Signature PDF invalide : %s", filename)
        return False

    return True
# ============================================================
# TRAITEMENT DES PIÃˆCES JOINTES
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
                            "Impossible de dÃ©coder la piÃ¨ce jointe : %s",
                            filename,
                        )
                        content = None


                    if content is not None and is_valid_file(filename, content):
                        registered_download = get_registered_download(
                            message_id, part_key
                        )

                        if was_downloaded(message_id, part_key):
                            logger.info("DÃ©jÃ  tÃ©lÃ©chargÃ© : %s", filename)
                        else:
                            file_hash = hashlib.sha256(content).hexdigest()
                            unique_prefix = hashlib.sha256(
                                f"{message_id}:{part_key}".encode("utf-8")
                            ).hexdigest()[:8]

                            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

                            safe_name = sanitize_filename(filename)
                            base_path = DOWNLOAD_DIR / safe_name
                            recovered_path = (
                                DOWNLOAD_DIR
                                / f"{base_path.stem}_{unique_prefix}"
                                f"{base_path.suffix}"
                            )

                            destination = None


                            # RÃ©parer le fichier dÃ©jÃ  associÃ© Ã  cette piÃ¨ce jointe,
                            # uniquement si son chemin est dans le dossier prÃ©vu.
                            if registered_download is not None:
                                registered_path, registered_hash = registered_download

                                try:
                                    registered_path = registered_path.resolve()
                                    download_root = DOWNLOAD_DIR.resolve()

                                    if (
                                        registered_path.parent == download_root
                                        and registered_path.is_file()
                                    ):
                                        current_hash = hashlib.sha256(
                                            registered_path.read_bytes()
                                        ).hexdigest()

                                        if current_hash != file_hash:
                                            destination = registered_path

                                except OSError:
                                    logger.exception(
                                        "Impossible de vÃ©rifier le fichier enregistrÃ©."
                                    )


                            # RÃ©utiliser un fichier intact laissÃ© par un essai prÃ©cÃ©dent.
                            if destination is None:
                                for candidate in (base_path, recovered_path):
                                    if candidate.is_file():
                                        try:
                                            existing_hash = hashlib.sha256(
                                                candidate.read_bytes()
                                            ).hexdigest()
                                        except OSError:
                                            logger.exception(
                                                "Impossible de vÃ©rifier le fichier : %s",
                                                candidate,
                                            )
                                            continue

                                        if existing_hash == file_hash:
                                            destination = candidate
                                            break

                            if destination is None:
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
                                    safe_name,
                                    file_hash,
                                    destination,
                                )
                                logger.info(
                                    "TÃ©lÃ©chargÃ© : %s",
                                    destination.name,
                                )
                            except (OSError, sqlite3.Error):
                                logger.exception(
                                    "Erreur d'enregistrement du fichier "
                                    "ou de l'historique SQLite : %s",
                                    filename,
                                )
                                print("DEBUG erreur d'enregistrement")

            nested_parts = part.get("parts", [])
            if nested_parts:
                process_parts(nested_parts, part_key)
# Traiter les piÃ¨ces jointes habituelles contenues dans "parts".
    process_parts(payload.get("parts", []))
    # Certains e-mails contiennent une seule piÃ¨ce jointe directement.
    if payload.get("filename"):
        process_parts([payload])
    # ============================================================
# VÃ‰RIFICATION PÃ‰RIODIQUE
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
        "VÃ©rification terminÃ©e. Messages traitÃ©s : %s",
        processed_count,
    )


# ============================================================
# POINT D'ENTRÃ‰E
# ============================================================

def main():
    logger.info("FIDOMEK ONE dÃ©marre.")
    logger.info("Mode test : %s", TEST_MODE)
    logger.info("Dossier de destination : %s", DOWNLOAD_DIR)
    logger.info("Base de donnÃ©es : %s", DATABASE_FILE)

    initialize_database()
    service = authenticate_gmail()


    while True:
        try:
            check_emails(service)
        except HttpError:
            logger.exception("Erreur lors de la vÃ©rification Gmail.")
        except Exception:
            logger.exception("Erreur inattendue pendant la vÃ©rification.")

        logger.info(
            "Prochaine vÃ©rification dans %s secondes.",
            CHECK_INTERVAL_SECONDS,
        )
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
