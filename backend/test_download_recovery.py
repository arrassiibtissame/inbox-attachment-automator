
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
                SELECT message_id, saved_path, file_hash
                FROM downloads
                WHERE message_id IN (?, ?)
                ORDER BY message_id
                """,
                ("message-test-001", "message-test-002"),
            ).fetchall()

        expected_hash = hashlib.sha256(content).hexdigest()

        # Un seul fichier physique pour le contenu identique.
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), content)

        # Chaque message doit avoir son propre historique.
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [row[0] for row in rows],
            ["message-test-001", "message-test-002"],
        )

        for message_id, saved_path, file_hash in rows:
            with self.subTest(message_id=message_id):
                self.assertTrue(Path(saved_path).is_file())
                self.assertEqual(Path(saved_path), files[0])
                self.assertEqual(file_hash, expected_hash)


    
    
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

        # Deux messages différents contenant le même PDF.
        app.process_message(service, "message-test-001")
        app.process_message(service, "message-test-002")

        original_file = self.test_download_dir / "facture.pdf"
        self.assertTrue(original_file.is_file())
        original_file.unlink()

        # L'application doit récupérer le fichier manquant.
        app.process_message(service, "message-test-001")

        recovered_files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(recovered_files), 1)
        self.assertEqual(recovered_files[0].read_bytes(), content)

        # Vérifier que les deux entrées SQLite restent cohérentes.
        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                """
                SELECT message_id, saved_path, file_hash
                FROM downloads
                WHERE message_id IN (?, ?)
                ORDER BY message_id
                """,
                ("message-test-001", "message-test-002"),
            ).fetchall()

        self.assertEqual(len(rows), 2)

        expected_hash = hashlib.sha256(content).hexdigest()

        for message_id, saved_path, file_hash in rows:
            with self.subTest(message_id=message_id):
                recovered_path = Path(saved_path)

                self.assertTrue(
                    recovered_path.is_file(),
                    f"Fichier manquant pour {message_id}: {saved_path}",
                )
                self.assertEqual(recovered_path.read_bytes(), content)
                self.assertEqual(file_hash, expected_hash)
                self.assertEqual(
                    hashlib.sha256(
                        recovered_path.read_bytes()
                    ).hexdigest(),
                    file_hash,
                )




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

    
    def test_process_message_downloads_pdf_using_attachment_id(self):
        content = b"%PDF-1.4\nFacture Gmail simulee"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")

        message_id = "message-attachment-id-test"
        attachment_id = "attachment-test-001"

        service = Mock()

        # Le message Gmail contient une référence à la pièce jointe,
        # mais pas son contenu directement.
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "FIDOMEK_TEST"}
                ],
                "parts": [
                    {
                        "filename": "facture.pdf",
                        "mimeType": "application/pdf",
                        "body": {
                            "attachmentId": attachment_id,
                        },
                    }
                ],
            }
        }

        # Simulation de l'appel Gmail qui récupère le contenu.
        service.users().messages().attachments().get().execute.return_value = {
            "data": encoded_content,
        }

        app.process_message(service, message_id)

        # Vérifier le téléchargement du fichier.
        downloaded_files = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(downloaded_files), 1)
        self.assertEqual(downloaded_files[0].read_bytes(), content)

        # Vérifier l'historique SQLite.
        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                """
                SELECT filename, file_hash, saved_path
                FROM downloads
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchall()

        self.assertEqual(len(rows), 1)

        filename, file_hash, saved_path = rows[0]
        self.assertEqual(filename, "facture.pdf")
        self.assertEqual(
            file_hash,
            hashlib.sha256(content).hexdigest(),
        )
        self.assertTrue(Path(saved_path).is_file())
        self.assertEqual(Path(saved_path).read_bytes(), content)

    
    def test_file_remains_if_database_registration_fails(self):
        content = b"%PDF-1.4\nFacture test"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")
        message_id = "message-db-error-test"

        service = Mock()
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "FIDOMEK_TEST"}
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

        with patch.object(
            app,
            "register_download",
            side_effect=sqlite3.OperationalError(
                "Erreur SQLite simulée"
            ),
        ):
            app.process_message(service, message_id)

        downloaded_files = list(self.test_download_dir.glob("*.pdf"))

        # Observer si le fichier existe malgré l'échec SQLite.
        self.assertEqual(len(downloaded_files), 1)
        self.assertEqual(downloaded_files[0].read_bytes(), content)

        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                "SELECT message_id FROM downloads WHERE message_id = ?",
                (message_id,),
            ).fetchall()

        self.assertEqual(len(rows), 0)


    
    def test_retry_registers_history_without_duplicate_file(self):
        content = b"%PDF-1.4\nFacture test"
        encoded_content = base64.urlsafe_b64encode(content).decode("ascii")
        message_id = "message-retry-history-test"

        service = Mock()
        service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "FIDOMEK_TEST"}
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

        # Premier passage : le fichier est écrit, mais SQLite échoue.
        with patch.object(
            app,
            "register_download",
            side_effect=sqlite3.OperationalError(
                "Erreur SQLite simulée"
            ),
        ):
            app.process_message(service, message_id)

        files_after_first_attempt = list(
            self.test_download_dir.glob("*.pdf")
        )
        self.assertEqual(len(files_after_first_attempt), 1)
        self.assertEqual(files_after_first_attempt[0].read_bytes(), content)

        # Deuxième passage : l'enregistrement doit réussir.
        app.process_message(service, message_id)

        files_after_retry = list(self.test_download_dir.glob("*.pdf"))
        self.assertEqual(len(files_after_retry), 1)

        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                """
                SELECT filename, file_hash, saved_path
                FROM downloads
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchall()

        self.assertEqual(len(rows), 1)
        filename, file_hash, saved_path = rows[0]
        self.assertEqual(filename, "facture.pdf")
        self.assertEqual(file_hash, hashlib.sha256(content).hexdigest())
        self.assertTrue(Path(saved_path).is_file())
        self.assertEqual(Path(saved_path).read_bytes(), content)

    
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
