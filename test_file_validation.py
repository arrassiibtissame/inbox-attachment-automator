
from pathlib import Path

import download_attachments as app


def test_allowed_extensions_are_accepted():
    for extension in app.ALLOWED_EXTENSIONS:
        if extension == ".pdf":
            content = b"%PDF-1.4 test"
        else:
            content = b"contenu de test non vide"

        assert app.is_valid_file(
            f"document{extension}", content
        ), f"L'extension {extension} devrait être acceptée"


def test_unsupported_extension_is_rejected():
    assert not app.is_valid_file("script.exe", b"contenu")


def test_empty_file_is_rejected():
    assert not app.is_valid_file("facture.pdf", b"")


def test_pdf_with_invalid_signature_is_rejected():
    assert not app.is_valid_file(
        "facture.pdf", b"ceci n'est pas un PDF"
    )


def test_pdf_with_valid_signature_is_accepted():
    assert app.is_valid_file(
        "facture.pdf", b"%PDF-1.4 contenu de test"
    )


def test_file_over_maximum_size_is_rejected():
    content = b"x" * (app.MAX_FILE_SIZE + 1)

    assert not app.is_valid_file("document.csv", content)


def test_file_at_maximum_size_is_accepted():
    content = b"x" * app.MAX_FILE_SIZE

    assert app.is_valid_file("document.csv", content)


def test_filename_is_sanitized():
    result = app.sanitize_filename(
        'facture<>:"/\\|?*.pdf'
    )

    assert Path(result).name == result
    assert not any(
        character in result
        for character in '<>:"/\\|?*'
    )


def test_empty_filename_gets_fallback_name():
    assert app.sanitize_filename("   ") == "document_sans_nom"


def test_filename_length_is_limited():
    result = app.sanitize_filename("a" * 250 + ".pdf")

    assert len(result) <= 180


def test_unique_file_path_does_not_overwrite_existing_file(tmp_path):
    existing = tmp_path / "facture.pdf"
    existing.write_bytes(b"premier fichier")

    result = app.unique_file_path(
        tmp_path, "facture.pdf", "message123"
    )

    assert result != existing
    assert not result.exists()
    assert existing.read_bytes() == b"premier fichier"
