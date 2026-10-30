import base64
import hashlib
import logging
import re
import sqlite3
import time
from contextlib import closing
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

BASE_DIR = Path(__file__).resolve().parent.parent

CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token_cabinet.json"
DATABASE_FILE = BASE_DIR / "downloads.db"

DOWNLOAD_DIR = Path.home() / "Documents" / "Cabinet-Documents-Test"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TIMEZONE = ZoneInfo("Africa/Casablanca")

# IMPORTANT : ne pas lancer le traitement réel pendant les tests.
TEST_MODE = False

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
# BASE DE DONNEES
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
    """Retourne le chemin et le hash enregistrés."""
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


def get_downloaded_documents():
    """Récupérer les documents enregistrés dans SQLite."""

    documents = []

    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT rowid, filename, saved_path, downloaded_at
            FROM downloads
            ORDER BY downloaded_at DESC
            """
        ).fetchall()

    for row in rows:
        file_path = Path(row["saved_path"])

        extension = file_path.suffix.lower()

        if extension == ".pdf":
            document_type = "PDF"
        elif extension in {".xls", ".xlsx", ".csv"}:
            document_type = "Excel"
        elif extension in {".doc", ".docx"}:
            document_type = "Word"
        else:
            document_type = "Image"

        try:
            size_bytes = file_path.stat().st_size
            size = f"{size_bytes / 1024:.1f} KB"
        except OSError:
            size = "Fichier introuvable"

        try:
            downloaded_at = datetime.fromisoformat(
                row["downloaded_at"]
            )
            date = downloaded_at.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            date = "Date inconnue"

        documents.append({
            "id": row["rowid"],
            "name": row["filename"],
            "client": "Non attribué",
            "type": document_type,
            "date": date,
            "size": size,
            "status": "À vérifier",
            "path": str(file_path),
        })

    return documents



def can_restore_registered_file(saved_path, expected_hash):
    """
    Autorise la restauration si tous les enregistrements qui pointent
    vers ce chemin attendent le même contenu.
    """
    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        cursor = connection.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN file_hash = ? THEN 1 ELSE 0 END)
            FROM downloads
            WHERE saved_path = ?
            """,
            (expected_hash, str(saved_path)),
        )
        total, matching = cursor.fetchone()

    return total > 0 and matching == total


def register_download(
    message_id,
    part_key,
    filename,
    file_hash,
    saved_path,
):
    """Crée ou actualise l'historique d'une pièce jointe."""
    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        with connection:
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


# ============================================================
# RECHERCHE DES EMAILS DU JOUR
# ============================================================

def build_gmail_query():
    now = datetime.now(TIMEZONE)

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
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
    """Retourne un chemin qui n'écrase pas un fichier existant."""
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
    """Vérifie l'extension, la taille et quelques critères simples."""
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


def find_existing_file(directory, filename, expected_hash):
    """Cherche un fichier de même extension et de même contenu."""
    extension = Path(filename).suffix.lower()

    try:
        candidates = list(directory.iterdir())
    except OSError:
        logger.exception(
            "Impossible de parcourir le dossier : %s",
            directory,
        )
        return None

    for candidate in candidates:
        if not candidate.is_file():
            continue

        if candidate.suffix.lower() != extension:
            continue

        try:
            current_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError:
            logger.warning(
                "Impossible de vérifier le fichier : %s",
                candidate,
                exc_info=True,
            )
            continue

        if current_hash == expected_hash:
            return candidate

    return None


# ============================================================
# TRAITEMENT DES PIECES JOINTES
# ============================================================

def process_message(service, message_id):
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
            part_key = (
                f"{parent_key}.{index}" if parent_key else str(index)
            )
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
                        file_hash = hashlib.sha256(content).hexdigest()

                        if was_downloaded(message_id, part_key):
                            logger.info("Déjà téléchargé : %s", filename)
                        else:
                            safe_name = sanitize_filename(filename)
                            unique_prefix = hashlib.sha256(
                                f"{message_id}:{part_key}".encode("utf-8")
                            ).hexdigest()[:8]

                            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
                            destination = None

                            # 1. Récupérer le chemin déjà enregistré si
                            # tous les enregistrements associés attendent
                            # le même contenu. Cela restaure un fichier
                            # modifié ou supprimé sans créer de doublon.
                            registered_download = get_registered_download(
                                message_id,
                                part_key,
                            )

                            if registered_download is not None:
                                registered_path, _ = registered_download
                                original_registered_path = registered_path

                                try:
                                    registered_path = registered_path.resolve()
                                    download_root = DOWNLOAD_DIR.resolve()

                                    if (
                                        registered_path.parent == download_root
                                        and can_restore_registered_file(
                                            original_registered_path,
                                            file_hash,
                                        )
                                    ):
                                        destination = registered_path

                                except (OSError, sqlite3.Error):
                                    logger.warning(
                                        "Impossible de vérifier le fichier "
                                        "enregistré : %s",
                                        original_registered_path,
                                        exc_info=True,
                                    )

                            # 2. Rechercher un autre fichier déjà présent
                            # qui possède exactement le même contenu.
                            if destination is None:
                                destination = find_existing_file(
                                    DOWNLOAD_DIR,
                                    safe_name,
                                    file_hash,
                                )

                            # 3. Aucun fichier identique : choisir un chemin
                            # libre sans écraser un document différent.
                            if destination is None:
                                destination = unique_file_path(
                                    DOWNLOAD_DIR,
                                    safe_name,
                                    unique_prefix,
                                )

                            file_already_exists = False

                            if destination.is_file():
                                try:
                                    existing_hash = hashlib.sha256(
                                        destination.read_bytes()
                                    ).hexdigest()
                                    file_already_exists = (
                                        existing_hash == file_hash
                                    )
                                except OSError:
                                    logger.exception(
                                        "Impossible de lire le fichier : %s",
                                        destination,
                                    )
                                    continue

                            # Écrire le contenu reçu si le fichier est absent
                            # ou si son contenu est différent.
                            if not file_already_exists:
                                try:
                                    destination.write_bytes(content)
                                except OSError:
                                    logger.exception(
                                        "Impossible d'écrire le fichier : %s",
                                        filename,
                                    )
                                    continue

                            # Enregistrer l'historique SQLite.
                            try:
                                register_download(
                                    message_id,
                                    part_key,
                                    safe_name,
                                    file_hash,
                                    destination,
                                )
                            except sqlite3.Error:
                                logger.exception(
                                    "Erreur d'enregistrement dans "
                                    "l'historique SQLite : %s",
                                    destination,
                                )
                                continue

                            if file_already_exists:
                                logger.info(
                                    "Fichier existant réutilisé : %s",
                                    destination.name,
                                )
                            else:
                                logger.info("Téléchargé : %s", destination.name)

            # Traiter aussi les pièces jointes des sous-parties MIME.
            nested_parts = part.get("parts", [])
            if nested_parts:
                process_parts(nested_parts, part_key)

    process_parts(payload.get("parts", []))

    # Traiter également un éventuel fichier directement dans le payload.
    if payload.get("filename"):
        process_parts([payload])


# ============================================================
# VERIFICATION PERIODIQUE
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
# POINT D'ENTREE
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
            logger.exception(
                "Erreur inattendue pendant la vérification."
            )

        logger.info(
            "Prochaine vérification dans %s secondes.",
            CHECK_INTERVAL_SECONDS,
        )
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

def get_downloaded_documents():
    """Récupérer les documents téléchargés depuis SQLite."""

    documents = []

    with closing(sqlite3.connect(DATABASE_FILE)) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT rowid, filename, file_hash, saved_path, downloaded_at
            FROM downloads
            ORDER BY downloaded_at DESC
            """
        ).fetchall()

    for row in rows:
        file_path = Path(row["saved_path"])
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            document_type = "PDF"
        elif extension in {".xls", ".xlsx", ".csv"}:
            document_type = "Excel"
        elif extension in {".doc", ".docx"}:
            document_type = "Word"
        elif extension in {".jpg", ".jpeg", ".png", ".webp"}:
            document_type = "Image"
        else:
            document_type = "Autre"

        try:
            size_bytes = file_path.stat().st_size
            size = f"{size_bytes / 1024:.1f} KB"
        except OSError:
            size = "Fichier introuvable"

        try:
            downloaded_at = datetime.fromisoformat(
                row["downloaded_at"]
            )
            date = downloaded_at.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            date = "Date inconnue"

        documents.append({
            "id": row["rowid"],
            "name": row["filename"],
            "client": "Non attribué",
            "type": document_type,
            "date": date,
            "size": size,
            "status": "À vérifier",
            "path": str(file_path),
            "file_hash": row["file_hash"],
        })

    return documents
