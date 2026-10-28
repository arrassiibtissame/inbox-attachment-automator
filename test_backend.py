
import sqlite3

import pytest

import download_attachments as app


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Prépare une base SQLite temporaire pour chaque test."""
    database_file = tmp_path / "test_downloads.db"
    download_dir = tmp_path / "downloads"

    monkeypatch.setattr(app, "DATABASE_FILE", database_file)
    monkeypatch.setattr(app, "DOWNLOAD_DIR", download_dir)

    app.initialize_database()

    return database_file, download_dir


# --------------------------------------------------
# Tests de sanitize_filename()
# --------------------------------------------------

def test_sanitize_filename_keeps_normal_filename():
    assert app.sanitize_filename("facture.pdf") == "facture.pdf"


def test_sanitize_filename_replaces_forbidden_characters():
    result = app.sanitize_filename('facture:2026?.pdf')

    assert ":" not in result
    assert "?" not in result
    assert result.endswith(".pdf")


def test_sanitize_filename_removes_path_components():
    result = app.sanitize_filename("../facture.pdf")

    assert result == "facture.pdf"


def test_sanitize_filename_handles_empty_name():
    assert app.sanitize_filename("   ") == "document_sans_nom"


def test_sanitize_filename_limits_length():
    result = app.sanitize_filename("a" * 200 + ".pdf")

    assert len(result) == 180


# --------------------------------------------------
# Tests de is_valid_file()
# --------------------------------------------------

def test_is_valid_file_accepts_valid_pdf():
    assert app.is_valid_file(
        "facture.pdf",
        b"%PDF-1.7\ncontenu de test",
    ) is True


def test_is_valid_file_rejects_empty_file():
    assert app.is_valid_file("facture.pdf", b"") is False


def test_is_valid_file_rejects_invalid_pdf_signature():
    assert app.is_valid_file(
        "facture.pdf",
        b"ceci n'est pas un PDF",
    ) is False


def test_is_valid_file_rejects_unsupported_extension():
    assert app.is_valid_file("script.exe", b"contenu") is False


def test_is_valid_file_rejects_oversized_file():
    content = b"x" * (app.MAX_FILE_SIZE + 1)

    assert app.is_valid_file("facture.pdf", content) is False


# --------------------------------------------------
# Tests SQLite : register_download() et was_downloaded()
# --------------------------------------------------

def test_register_download_creates_database_record(
    isolated_database, tmp_path
):
    saved_file = tmp_path / "facture.pdf"
    saved_file.write_bytes(b"%PDF-1.7\ncontenu de test")

    app.register_download(
        "message-1",
        "part-1",
        "facture.pdf",
        "hash-123",
        saved_file,
    )

    with sqlite3.connect(app.DATABASE_FILE) as connection:
        row = connection.execute(
            """
            SELECT message_id, part_key, filename, file_hash, saved_path
            FROM downloads
            WHERE message_id = ? AND part_key = ?
            """,
            ("message-1", "part-1"),
        ).fetchone()

    assert row == (
        "message-1",
        "part-1",
        "facture.pdf",
        "hash-123",
        str(saved_file),
    )


def test_register_download_updates_existing_record(
    isolated_database, tmp_path
):
    first_file = tmp_path / "facture_v1.pdf"
    second_file = tmp_path / "facture_v2.pdf"

    first_file.write_bytes(b"%PDF-1.7\nversion 1")
    second_file.write_bytes(b"%PDF-1.7\nversion 2")

    app.register_download(
        "message-1", "part-1", "facture_v1.pdf",
        "hash-1", first_file,
    )
    app.register_download(
        "message-1", "part-1", "facture_v2.pdf",
        "hash-2", second_file,
    )

    with sqlite3.connect(app.DATABASE_FILE) as connection:
        rows = connection.execute(
            """
            SELECT filename, file_hash, saved_path
            FROM downloads
            WHERE message_id = ? AND part_key = ?
            """,
            ("message-1", "part-1"),
        ).fetchall()

    assert rows == [
        ("facture_v2.pdf", "hash-2", str(second_file))
    ]




def test_was_downloaded_returns_true_when_file_exists(
    isolated_database, tmp_path
):
    saved_file = tmp_path / "facture.pdf"
    saved_file.write_bytes(b"%PDF-1.7\ncontenu")

    # Calculer le vrai SHA-256 du fichier
    file_hash = app.hashlib.sha256(saved_file.read_bytes()).hexdigest()

    app.register_download(
        "message-1",
        "part-1",
        "facture.pdf",
        file_hash,
        saved_file,
    )

    assert app.was_downloaded("message-1", "part-1") is True




def test_was_downloaded_returns_false_when_file_is_missing(
    isolated_database, tmp_path
):
    saved_file = tmp_path / "facture.pdf"
    saved_file.write_bytes(b"%PDF-1.7\ncontenu")

    app.register_download(
        "message-1", "part-1", "facture.pdf",
        "hash-123", saved_file,
    )

    saved_file.unlink()

    assert app.was_downloaded("message-1", "part-1") is False


def test_was_downloaded_returns_false_for_unknown_record(
    isolated_database,
):
    assert app.was_downloaded("unknown-message", "part-1") is False


# --------------------------------------------------
# Tests de unique_file_path()
# --------------------------------------------------

def test_unique_file_path_returns_original_path_when_available(
    tmp_path,
):
    result = app.unique_file_path(
        tmp_path, "facture.pdf", "message-1"
    )

    assert result == tmp_path / "facture.pdf"


def test_unique_file_path_avoids_overwriting_existing_file(
    tmp_path,
):
    original = tmp_path / "facture.pdf"
    original.write_bytes(b"document original")

    result = app.unique_file_path(
        tmp_path, "facture.pdf", "message-1"
    )

    assert result != original
    assert not result.exists()
    assert original.read_bytes() == b"document original"


def test_unique_file_path_handles_repeated_collisions(tmp_path):
    (tmp_path / "facture.pdf").write_bytes(b"original")
    (tmp_path / "facture_message-1.pdf").write_bytes(b"collision")

    result = app.unique_file_path(
        tmp_path, "facture.pdf", "message-1"
    )

    assert result == tmp_path / "facture_message-1_1.pdf"
    assert not result.exists()
