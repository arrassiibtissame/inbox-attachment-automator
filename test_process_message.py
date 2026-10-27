
import base64
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import download_attachments as app


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeAttachments:
    def __init__(self, attachment_data=None):
        self.attachment_data = attachment_data or {}

    def get(self, userId, messageId, id):
        return FakeRequest({"data": self.attachment_data[id]})


class FakeMessages:
    def __init__(self, message, attachment_data=None):
        self.message = message
        self.fake_attachments = FakeAttachments(attachment_data)

    def get(self, userId, id, format):
        return FakeRequest(self.message)

    def attachments(self):
        return self.fake_attachments


class FakeUsers:
    def __init__(self, message, attachment_data=None):
        self.fake_messages = FakeMessages(message, attachment_data)

    def messages(self):
        return self.fake_messages


class FakeGmailService:
    def __init__(self, message, attachment_data=None):
        self.fake_users = FakeUsers(message, attachment_data)

    def users(self):
        return self.fake_users


class TestProcessMessage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.test_db = self.root / "test.db"
        self.test_download_dir = self.root / "documents"

        self.db_patch = patch.object(app, "DATABASE_FILE", self.test_db)
        self.dir_patch = patch.object(
            app, "DOWNLOAD_DIR", self.test_download_dir
        )

        self.db_patch.start()
        self.dir_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.dir_patch.stop)

        app.initialize_database()

    def make_service(self, filename, content):
        encoded = base64.urlsafe_b64encode(content).decode("ascii")

        message = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test FIDOMEK"}
                ],
                "parts": [
                    {
                        "filename": filename,
                        "body": {"data": encoded},
                    }
                ],
            }
        }

        return FakeGmailService(message)

    def test_valid_pdf_is_saved_and_registered(self):
        content = b"%PDF-1.4 test document"
        service = self.make_service("facture.pdf", content)

        app.process_message(service, "message-001")

        saved_files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)

        with closing(sqlite3.connect(self.test_db)) as connection:
            row = connection.execute(
                """
                SELECT filename, file_hash
                FROM downloads
                WHERE message_id = ?
                """,
                ("message-001",),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "facture.pdf")
        self.assertEqual(row[1], hashlib.sha256(content).hexdigest())

    def test_unsupported_file_is_not_saved(self):
        service = self.make_service("programme.exe", b"not allowed")

        app.process_message(service, "message-002")

        self.assertEqual(list(self.test_download_dir.iterdir()), [])

        with closing(sqlite3.connect(self.test_db)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM downloads"
            ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_invalid_pdf_is_not_saved(self):
        service = self.make_service("facture.pdf", b"not a PDF")

        app.process_message(service, "message-003")

        self.assertEqual(list(self.test_download_dir.iterdir()), [])

    def test_nested_attachment_is_processed(self):
        content = b"%PDF-1.4 nested"
        encoded = base64.urlsafe_b64encode(content).decode("ascii")

        message = {
            "payload": {
                "headers": [],
                "parts": [
                    {
                        "mimeType": "multipart/mixed",
                        "parts": [
                            {
                                "filename": "nested.pdf",
                                "body": {"data": encoded},
                            }
                        ],
                    }
                ],
            }
        }

        service = FakeGmailService(message)
        app.process_message(service, "message-004")

        saved_files = list(self.test_download_dir.glob("nested.pdf"))
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)

    
    def test_attachment_id_is_downloaded(self):
        content = b"%PDF-1.4 attachment API"
        encoded = base64.urlsafe_b64encode(content).decode("ascii")

        message = {
            "payload": {
                "headers": [],
                "parts": [
                    {
                        "filename": "attachment.pdf",
                        "body": {"attachmentId": "attachment-123"},
                    }
                ],
            }
        }

        service = FakeGmailService(
            message,
            {"attachment-123": encoded},
        )

        app.process_message(service, "message-005")

        saved_files = list(
            self.test_download_dir.glob("attachment.pdf")
        )

        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)

    def test_processing_same_message_twice_does_not_duplicate_file(self):
        content = b"%PDF-1.4 duplicate test"
        service = self.make_service("facture.pdf", content)

        app.process_message(service, "message-006")
        app.process_message(service, "message-006")

        saved_files = list(self.test_download_dir.glob("*.pdf"))

        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)

    
    def test_modified_saved_file_is_recovered_without_duplicate(self):
        content = b"%PDF-1.4 duplicate test"
        service = self.make_service("facture.pdf", content)

        app.process_message(service, "message-modified")

        saved_file = self.test_download_dir / "facture.pdf"
        self.assertTrue(saved_file.exists())

        # Simule une modification du fichier déjà enregistré.
        saved_file.write_bytes(b"%PDF-1.4 contenu modifie")

        app.process_message(service, "message-modified")

        saved_files = list(self.test_download_dir.glob("*.pdf"))

        # Le document reçu de Gmail doit être récupéré sans doublon.
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)
     

    
    def test_database_failure_after_file_write_is_handled(self):
        content = b"%PDF-1.4 test document"
        service = self.make_service("facture.pdf", content)

        with patch.object(
            app,
            "register_download",
            side_effect=sqlite3.OperationalError(
                "Simulated database failure"
            ),
        ):
            with self.assertLogs(app.logger, level="ERROR") as logs:
                app.process_message(service, "message-db-error")

        saved_files = list(self.test_download_dir.glob("*.pdf"))

        # Ce test documente le comportement actuel :
        # le fichier est écrit avant l'échec de SQLite.
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].read_bytes(), content)

        self.assertTrue(
            any("Erreur d'enregistrement" in line for line in logs.output)
        )
        
    
    def test_retry_after_database_failure_does_not_create_duplicate(self):
        content = b"%PDF-1.4 test document"
        service = self.make_service("facture.pdf", content)

        # Premier essai : le fichier est écrit, mais SQLite échoue.
        with patch.object(
            app,
            "register_download",
            side_effect=sqlite3.OperationalError(
                "Simulated database failure"
            ),
        ):
            with self.assertLogs(app.logger, level="ERROR"):
                app.process_message(service, "message-retry")

        files_after_first_attempt = list(
            self.test_download_dir.glob("*.pdf")
        )
        self.assertEqual(len(files_after_first_attempt), 1)

        # Deuxième essai : utilise le véritable SQLite temporaire.
        app.process_message(service, "message-retry")

        files_after_second_attempt = list(
            self.test_download_dir.glob("*.pdf")
        )
        self.assertEqual(len(files_after_second_attempt), 1)
        self.assertEqual(files_after_second_attempt[0].read_bytes(), content)

        with closing(sqlite3.connect(self.test_db)) as connection:
            row = connection.execute(
                """
                SELECT filename, file_hash, saved_path
                FROM downloads
                WHERE message_id = ? AND part_key = ?
                """,
                ("message-retry", "0"),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "facture.pdf")
        self.assertEqual(row[1], hashlib.sha256(content).hexdigest())
        self.assertEqual(Path(row[2]), files_after_second_attempt[0])


    def test_existing_different_file_is_not_overwritten(self):
        content = b"%PDF-1.4 new document"
        service = self.make_service("facture.pdf", content)

        self.test_download_dir.mkdir(parents=True, exist_ok=True)
        existing_file = self.test_download_dir / "facture.pdf"
        existing_content = b"%PDF-1.4 different document"
        existing_file.write_bytes(existing_content)

        app.process_message(service, "message-different-file")

        # Le fichier existant doit rester intact.
        self.assertEqual(existing_file.read_bytes(), existing_content)

        # Le nouveau document doit être enregistré séparément.
        saved_files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(saved_files), 2)

        new_file = next(
            path for path in saved_files if path != existing_file
        )
        self.assertEqual(new_file.read_bytes(), content)



if __name__ == "__main__":
    unittest.main()
