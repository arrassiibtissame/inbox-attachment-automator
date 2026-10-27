import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import download_attachments as app


class TestDatabase(unittest.TestCase):

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

    def test_initialize_database_creates_downloads_table(self):
        with closing(sqlite3.connect(self.test_db)) as connection:
            row = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'downloads'
                """
            ).fetchone()

        self.assertIsNotNone(row)

    def test_register_download_inserts_history(self):
        document = self.test_download_dir / "facture.pdf"
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

    def test_register_download_updates_existing_record(self):
        first = self.test_download_dir / "first.pdf"
        second = self.test_download_dir / "second.pdf"

        first.write_bytes(b"%PDF-1.4 first")
        second.write_bytes(b"%PDF-1.4 second")

        app.register_download(
            self.message_id,
            self.part_key,
            "first.pdf",
            hashlib.sha256(first.read_bytes()).hexdigest(),
            str(first),
        )

        app.register_download(
            self.message_id,
            self.part_key,
            "second.pdf",
            hashlib.sha256(second.read_bytes()).hexdigest(),
            str(second),
        )

        with closing(sqlite3.connect(self.test_db)) as connection:
            rows = connection.execute(
                """
                SELECT filename, file_hash, saved_path
                FROM downloads
                WHERE message_id = ? AND part_key = ?
                """,
                (self.message_id, self.part_key),
            ).fetchall()

        self.assertEqual(
            rows,
            [("second.pdf", hashlib.sha256(second.read_bytes()).hexdigest(), str(second))],
        )

    def test_different_parts_of_same_message_are_distinct(self):
        first = self.test_download_dir / "facture.pdf"
        second = self.test_download_dir / "releve.pdf"

        first.write_bytes(b"%PDF-1.4 facture")
        second.write_bytes(b"%PDF-1.4 releve")

        app.register_download(
            self.message_id,
            "part-1",
            "facture.pdf",
            hashlib.sha256(first.read_bytes()).hexdigest(),
            str(first),
        )

        app.register_download(
            self.message_id,
            "part-2",
            "releve.pdf",
            hashlib.sha256(second.read_bytes()).hexdigest(),
            str(second),
        )

        with closing(sqlite3.connect(self.test_db)) as connection:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM downloads
                WHERE message_id = ?
                """,
                (self.message_id,),
            ).fetchone()[0]

        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
