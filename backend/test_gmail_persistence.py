
import hashlib

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.connection import Base
import backend.database.models  # noqa: F401

from backend.database.models.file import File
from backend.database.models.document import Document, DocumentStatus
from backend.database.models.document_receipt import (
    DocumentReceipt,
    ReceiptSource,
)
from backend.database.models.document_event import DocumentEvent

from backend.services.gmail_service import GmailService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def gmail(tmp_path):
    service = GmailService()
    service.storage_dir = tmp_path
    return service


@pytest.fixture
def attachment_data():
    content = b"%PDF-1.4 FIDOMEK test document"

    return {
        "filename": "facture.pdf",
        "content": content,
        "mime_type": "application/pdf",
        "message_id": "gmail-message-001",
        "part_id": "0",
        "sender": "client@example.com",
        "subject": "Facture janvier",
        "thread_id": "thread-001",
        "received_at": "2026-11-10T10:00:00+00:00",
    }


def save(gmail, session, data, created_paths):
    return gmail.save_attachment(
        session,
        filename=data["filename"],
        content=data["content"],
        mime_type=data["mime_type"],
        message_id=data["message_id"],
        part_id=data["part_id"],
        sender=data["sender"],
        subject=data["subject"],
        thread_id=data["thread_id"],
        received_at=data["received_at"],
        created_paths=created_paths,
    )


def count(session, model):
    return session.scalar(
        select(func.count()).select_from(model)
    )


def test_save_attachment_creates_file_document_and_receipt(
    gmail, db_session, attachment_data
):
    created_paths = []

    with db_session.begin():
        result = save(
            gmail,
            db_session,
            attachment_data,
            created_paths,
        )

    assert result is True
    assert len(created_paths) == 1

    stored_file = db_session.scalars(select(File)).one()
    document = db_session.scalars(select(Document)).one()
    receipt = db_session.scalars(select(DocumentReceipt)).one()
    event = db_session.scalars(select(DocumentEvent)).one()

    assert stored_file.sha256 == hashlib.sha256(
        attachment_data["content"]
    ).hexdigest()

    assert stored_file.size_bytes == len(attachment_data["content"])
    assert stored_file.mime_type == "application/pdf"
    assert stored_file.extension == ".pdf"

    assert document.status == DocumentStatus.TO_REVIEW
    assert document.client_id is None

    assert receipt.document_id == document.id
    assert receipt.file_id == stored_file.id
    assert receipt.source == ReceiptSource.GMAIL
    assert receipt.source_message_id == attachment_data["message_id"]
    assert receipt.source_part_id == attachment_data["part_id"]
    assert receipt.sender == attachment_data["sender"]
    assert receipt.source_metadata["subject"] == attachment_data["subject"]

    assert event.document_id == document.id
    assert event.event_type == "DOCUMENT_RECEIVED"

    assert len(created_paths) == 1
    assert created_paths[0].is_file()
    assert created_paths[0].read_bytes() == attachment_data["content"]


def test_same_message_attachment_is_not_saved_twice(
    gmail, db_session, attachment_data
):
    created_paths = []

    with db_session.begin():
        first_result = save(
            gmail,
            db_session,
            attachment_data,
            created_paths,
        )

    with db_session.begin():
        second_result = save(
            gmail,
            db_session,
            attachment_data,
            created_paths,
        )

    assert first_result is True
    assert second_result is False

    assert count(db_session, File) == 1
    assert count(db_session, Document) == 1
    assert count(db_session, DocumentReceipt) == 1
    assert count(db_session, DocumentEvent) == 1
    assert len(created_paths) == 1


def test_same_content_from_another_message_reuses_file_and_document(
    gmail, db_session, attachment_data
):
    created_paths = []

    second_data = {
        **attachment_data,
        "message_id": "gmail-message-002",
        "part_id": "1",
        "subject": "Facture renvoyée",
    }

    with db_session.begin():
        save(gmail, db_session, attachment_data, created_paths)

    with db_session.begin():
        result = save(gmail, db_session, second_data, created_paths)

    assert result is True

    assert count(db_session, File) == 1
    assert count(db_session, Document) == 1
    assert count(db_session, DocumentReceipt) == 2
    assert count(db_session, DocumentEvent) == 1

    receipts = db_session.scalars(
        select(DocumentReceipt).order_by(DocumentReceipt.id)
    ).all()

    assert receipts[0].file_id == receipts[1].file_id
    assert receipts[0].document_id == receipts[1].document_id

    assert receipts[0].source_message_id == "gmail-message-001"
    assert receipts[1].source_message_id == "gmail-message-002"

    assert len(created_paths) == 1


def test_missing_existing_file_is_restored(
    gmail, db_session, attachment_data
):
    created_paths = []

    with db_session.begin():
        save(gmail, db_session, attachment_data, created_paths)

    original_path = created_paths[0]

    assert original_path.is_file()

    original_path.unlink()

    assert not original_path.exists()

    with db_session.begin():
        result = save(
            gmail,
            db_session,
            attachment_data,
            created_paths,
        )

    assert result is False
    assert original_path.is_file()
    assert original_path.read_bytes() == attachment_data["content"]

    assert count(db_session, File) == 1
    assert count(db_session, Document) == 1
    assert count(db_session, DocumentReceipt) == 1


def test_modified_existing_file_is_restored(
    gmail, db_session, attachment_data
):
    created_paths = []

    with db_session.begin():
        save(gmail, db_session, attachment_data, created_paths)

    original_path = created_paths[0]

    original_path.write_bytes(b"CONTENU MODIFIE")

    with db_session.begin():
        result = save(
            gmail,
            db_session,
            attachment_data,
            created_paths,
        )

    assert result is False
    assert original_path.read_bytes() == attachment_data["content"]

    assert count(db_session, File) == 1
    assert count(db_session, Document) == 1
    assert count(db_session, DocumentReceipt) == 1
