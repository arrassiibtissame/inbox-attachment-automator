
import hashlib
from importlib.resources import files
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
import base64
from unittest.mock import Mock

import download_attachments as app


class TestDownloadRecovery(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.test_db = self.root / "test_downloads.db"
        self.test_download_dir = self.root / "documents"

        self.db_patch = patch.object(
            app, "DATABASE_FILE", self.test_db
        )
        self.dir_patch = patch.object(
            app, "DOWNLOAD_DIR", self.test_download_dir
        )

        self.db_patch.start()
        self.dir_patch.start()

        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.dir_patch.stop)

        app.initialize_database()

        self.message_id = "message-test-001"
        self.part_key = "part-test-001"
   

   
    
    def test_processing_same_message_twice_does_not_duplicate_file(self):
        content = b"%PDF-1.4\nFacture de test"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")

        service = Mock()
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Facture de test"}
                ],
                "parts": [
                    {
                        "filename": "facture.pdf",
                        "mimeType": "application/pdf",
                        "body": {"data": encoded_content},
                    }
                ],
            }
        }

        app.process_message(service, self.message_id)
        app.process_message(service, self.message_id)

        files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), content)

        with closing(sqlite3.connect(self.test_db)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM downloads WHERE message_id = ?",
                (self.message_id,),
            ).fetchone()[0]

        self.assertEqual(count, 1)


    def test_register_download_creates_history(self):
        document = self.test_download_dir / "facture.pdf"
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_bytes(b"%PDF-1.4 test")

        file_hash = hashlib.sha256(document.read_bytes()).hexdigest()

        app.register_download(
            self.message_id,
            self.part_key,
            "facture.pdf",
            file_hash,
            str(document),
        )

        self.assertTrue(
            app.was_downloaded(self.message_id, self.part_key)
        )

    
    def test_register_download_creates_history(self):
        document = self.test_download_dir / "facture.pdf"
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_bytes(b"%PDF-1.4 test")

        file_hash = hashlib.sha256(document.read_bytes()).hexdigest()

        app.register_download(
            self.message_id,
            self.part_key,
            "facture.pdf",
            file_hash,
            str(document),
        )

        self.assertTrue(
            app.was_downloaded(self.message_id, self.part_key)
        )

   
    def test_register_download_updates_saved_path_and_hash(self):
        first = self.test_download_dir / "first.pdf"
        second = self.test_download_dir / "second.pdf"

        first.parent.mkdir(parents=True, exist_ok=True)
        first.write_bytes(b"%PDF-1.4 first")
        second.write_bytes(b"%PDF-1.4 second")

        hash_first = hashlib.sha256(first.read_bytes()).hexdigest()
        hash_second = hashlib.sha256(second.read_bytes()).hexdigest()

        app.register_download(
            self.message_id,
            self.part_key,
            "first.pdf",
            hash_first,
            str(first),
        )

        app.register_download(
            self.message_id,
            self.part_key,
            "second.pdf",
            hash_second,
            str(second),
        )

        with closing(sqlite3.connect(self.test_db)) as connection:
            row = connection.execute(
                """
                SELECT filename, file_hash, saved_path
                FROM downloads
                WHERE message_id = ? AND part_key = ?
                """,
                (self.message_id, self.part_key),
            ).fetchone()

        self.assertEqual(
            row,
            ("second.pdf", hash_second, str(second)),
        )

        self.assertTrue(
            app.was_downloaded(self.message_id, self.part_key)
        )

    
    def test_different_messages_with_same_pdf_content(self):
        content = b"%PDF-1.4\nFacture identique"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")

        service = Mock()
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Facture de test"}
                ],
                "parts": [
                    {
                        "filename": "facture.pdf",
                        "mimeType": "application/pdf",
                        "body": {"data": encoded_content},
                    }
                ],
            }
        }

        app.process_message(service, "message-test-001")
        app.process_message(service, "message-test-002")

        files = list(self.test_download_dir.glob("*.pdf"))

        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                """
                SELECT message_id, part_key, saved_path, file_hash
                FROM downloads
                WHERE message_id IN (?, ?)
                ORDER BY message_id
                """,
                ("message-test-001", "message-test-002"),
            ).fetchall()

        print("Fichiers physiques :", len(files))
        print("Entrées SQLite :", len(rows))
        print("Historique :", rows)

    
    def test_deleted_shared_file_is_recovered(self):
        content = b"%PDF-1.4\nFacture identique"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")

        service = Mock()
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Facture de test"}
                ],
                "parts": [
                    {
                        "filename": "facture.pdf",
                        "mimeType": "application/pdf",
                        "body": {"data": encoded_content},
                    }
                ],
            }
        }

        app.process_message(service, "message-test-001")
        app.process_message(service, "message-test-002")

        original_file = self.test_download_dir / "facture.pdf"
        self.assertTrue(original_file.is_file())
        original_file.unlink()

        app.process_message(service, "message-test-001")

        recovered_files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(recovered_files), 1)
        self.assertEqual(recovered_files[0].read_bytes(), content)



    def test_deleted_file_is_no_longer_detected_as_downloaded(self):
        document = self.test_download_dir / "facture.pdf"
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_bytes(b"%PDF-1.4 test")

        app.register_download(
            self.message_id,
            self.part_key,
            "facture.pdf",
             hashlib.sha256(document.read_bytes()).hexdigest(),
            str(document),
        )

        self.assertTrue(
            app.was_downloaded(self.message_id, self.part_key)
        )

        document.unlink()

        self.assertFalse(
            app.was_downloaded(self.message_id, self.part_key)
        )
    
    def test_modified_file_is_not_trusted_as_downloaded(self):
        document = self.test_download_dir / "facture.pdf"
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_bytes(b"%PDF-1.4 original")

        app.register_download(
            self.message_id,
            self.part_key,
            "facture.pdf",
            hashlib.sha256(document.read_bytes()).hexdigest(),
            str(document),
        )

        self.assertTrue(
            app.was_downloaded(self.message_id, self.part_key)
        )

        # Le fichier existe toujours, mais son contenu a changé.
        document.write_bytes(b"%PDF-1.4 contenu modifie")

        self.assertFalse(
            app.was_downloaded(self.message_id, self.part_key)
        )

       


if __name__ == "__main__":
    unittest.main()
