
import base64
import hashlib
from unittest.mock import MagicMock

import pytest

from backend.services.gmail_service import GmailService


@pytest.fixture
def gmail():
    return GmailService()


def test_decode_attachment(gmail):
    original = b"Contenu du document"
    encoded = base64.urlsafe_b64encode(original).decode()
    assert gmail.decode_attachment(encoded) == original


def test_decode_empty_attachment(gmail):
    assert gmail.decode_attachment("") == b""


def test_sanitize_filename_removes_path(gmail):
    assert gmail.sanitize_filename("../facture.pdf") == "facture.pdf"


def test_sanitize_filename_replaces_invalid_characters(gmail):
    assert gmail.sanitize_filename('facture:test?.pdf') == "facture_test_.pdf"


def test_sanitize_filename_empty_name(gmail):
    assert gmail.sanitize_filename("   ") == "document_sans_nom"


def test_validate_valid_pdf(gmail):
    assert gmail.validate_file("facture.pdf", b"%PDF-1.4 contenu")


def test_validate_rejects_empty_file(gmail):
    assert not gmail.validate_file("facture.pdf", b"")


def test_validate_rejects_invalid_pdf(gmail):
    assert not gmail.validate_file("facture.pdf", b"Ce n'est pas un PDF")


def test_validate_rejects_unsupported_extension(gmail):
    assert not gmail.validate_file("document.exe", b"contenu")


def test_validate_rejects_oversized_file(gmail):
    gmail.max_file_size = 5
    assert not gmail.validate_file("facture.pdf", b"%PDF-1.4 contenu trop long")


def test_calculate_hash(gmail):
    content = b"document de test"
    assert gmail.calculate_hash(content) == hashlib.sha256(content).hexdigest()


def test_write_file(gmail, tmp_path):
    destination = tmp_path / "documents" / "facture.pdf"
    content = b"%PDF-1.4 contenu"

    gmail.write_file(destination, content)

    assert destination.exists()
    assert destination.read_bytes() == content
    assert not destination.with_name(destination.name + ".tmp").exists()


def test_get_header_is_case_insensitive(gmail):
    headers = [
        {"name": "From", "value": "client@example.com"},
        {"name": "Subject", "value": "Facture"},
    ]

    assert gmail.get_header(headers, "subject") == "Facture"
    assert gmail.get_header(headers, "FROM") == "client@example.com"


def test_extract_nested_attachment(gmail):
    content = b"%PDF-1.4 test"
    encoded = base64.urlsafe_b64encode(content).decode()

    payload = {
        "parts": [
            {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "filename": "facture.pdf",
                        "mimeType": "application/pdf",
                        "body": {"data": encoded},
                    }
                ],
            }
        ]
    }

    result = gmail.extract_attachments(MagicMock(), "message-123", payload)

    assert len(result) == 1
    assert result[0]["filename"] == "facture.pdf"
    assert result[0]["data"] == encoded
    assert result[0]["part_id"] == "0.0"



def test_extract_attachment_from_gmail_api(gmail):
    encoded = base64.urlsafe_b64encode(b"%PDF-1.4 test").decode()

    service = MagicMock()
    get_mock = service.users.return_value.messages.return_value.attachments.return_value.get

    get_mock.return_value.execute.return_value = {"data": encoded}

    payload = {
        "parts": [
            {
                "filename": "facture.pdf",
                "mimeType": "application/pdf",
                "body": {"attachmentId": "attachment-123"},
            }
        ]
    }

    result = gmail.extract_attachments(service, "message-123", payload)

    assert len(result) == 1
    assert result[0]["data"] == encoded

    get_mock.assert_called_once_with(
        userId="me",
        messageId="message-123",
        id="attachment-123",
    )
