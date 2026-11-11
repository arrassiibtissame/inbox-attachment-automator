
import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    Document,
    DocumentReceipt,
    DocumentStatus,
    File,
    ReceiptSource,
    User,
    UserRole,
)
from backend.database.repositories.document_receipt_repository import (
    DocumentReceiptRepository,
)


def create_document(db_session):
    document = Document(
        status=DocumentStatus.TO_REVIEW,
    )
    db_session.add(document)
    db_session.flush()
    return document


def create_file(db_session, **overrides):
    data = {
        "original_filename": "invoice.pdf",
        "stored_filename": "file_001.pdf",
        "storage_path": "storage/files/file_001.pdf",
        "sha256": "a" * 64,
        "extension": ".pdf",
        "size_bytes": 1024,
        "mime_type": "application/pdf",
    }

    data.update(overrides)

    file = File(**data)
    db_session.add(file)
    db_session.flush()
    return file


def create_receipt(repository, document_id, file_id, **overrides):
    data = {
        "source": ReceiptSource.GMAIL,
        "source_message_id": "message-001",
        "source_part_id": "part-001",
        "sender": "client@example.com",
        "source_metadata": {"subject": "Invoice"},
    }

    data.update(overrides)

    return repository.create(
        document_id=document_id,
        file_id=file_id,
        **data,
    )


def test_create_receipt(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file = create_file(db_session)

    receipt = create_receipt(
        repository,
        document.id,
        file.id,
    )

    assert receipt.id is not None
    assert receipt.document_id == document.id
    assert receipt.file_id == file.id
    assert receipt.source == ReceiptSource.GMAIL
    assert receipt.source_message_id == "message-001"
    assert receipt.source_part_id == "part-001"
    assert receipt.sender == "client@example.com"
    assert receipt.source_metadata == {"subject": "Invoice"}
    assert receipt.received_at is not None


def test_get_by_id(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file = create_file(db_session)

    receipt = create_receipt(repository, document.id, file.id)

    result = repository.get_by_id(receipt.id)

    assert result is not None
    assert result.id == receipt.id


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = DocumentReceiptRepository(db_session)

    assert repository.get_by_id(999) is None


def test_get_by_source_message_part(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file = create_file(db_session)

    receipt = create_receipt(repository, document.id, file.id)

    result = repository.get_by_source_message_part(
        source=ReceiptSource.GMAIL,
        source_message_id="message-001",
        source_part_id="part-001",
    )

    assert result is not None
    assert result.id == receipt.id


def test_get_by_source_message_part_returns_none_when_not_found(db_session):
    repository = DocumentReceiptRepository(db_session)

    result = repository.get_by_source_message_part(
        source=ReceiptSource.GMAIL,
        source_message_id="unknown-message",
        source_part_id="unknown-part",
    )

    assert result is None


def test_list_by_document(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file_a = create_file(db_session)
    file_b = create_file(
        db_session,
        original_filename="second.pdf",
        stored_filename="file_002.pdf",
        sha256="b" * 64,
    )

    first = create_receipt(
        repository,
        document.id,
        file_a.id,
    )

    second = create_receipt(
        repository,
        document.id,
        file_b.id,
        source_message_id="message-002",
        source_part_id="part-002",
    )

    results = repository.list_by_document(document.id)

    assert len(results) == 2
    assert {receipt.id for receipt in results} == {
        first.id,
        second.id,
    }


def test_list_by_file(db_session):
    repository = DocumentReceiptRepository(db_session)
    document_a = create_document(db_session)
    document_b = create_document(db_session)
    file = create_file(db_session)

    first = create_receipt(
        repository,
        document_a.id,
        file.id,
    )

    second = create_receipt(
        repository,
        document_b.id,
        file.id,
        source_message_id="message-002",
        source_part_id="part-002",
    )

    results = repository.list_by_file(file.id)

    assert len(results) == 2
    assert {receipt.id for receipt in results} == {
        first.id,
        second.id,
    }


def test_list_by_source(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    gmail_file = create_file(db_session)

    whatsapp_file = create_file(
        db_session,
        original_filename="whatsapp.pdf",
        stored_filename="file_002.pdf",
        sha256="b" * 64,
    )

    gmail_receipt = create_receipt(
        repository,
        document.id,
        gmail_file.id,
    )

    whatsapp_receipt = create_receipt(
        repository,
        document.id,
        whatsapp_file.id,
        source=ReceiptSource.WHATSAPP,
        source_message_id="whatsapp-message",
        source_part_id="whatsapp-part",
    )

    results = repository.list_by_source(ReceiptSource.GMAIL)

    assert len(results) == 1
    assert results[0].id == gmail_receipt.id
    assert results[0].id != whatsapp_receipt.id


def test_duplicate_source_message_part_is_rejected(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file_a = create_file(db_session)
    file_b = create_file(
        db_session,
        original_filename="second.pdf",
        stored_filename="file_002.pdf",
        sha256="b" * 64,
    )

    create_receipt(repository, document.id, file_a.id)

    with pytest.raises(IntegrityError):
        create_receipt(
            repository,
            document.id,
            file_b.id,
        )

    db_session.rollback()


def test_receipt_requires_existing_document(db_session):
    repository = DocumentReceiptRepository(db_session)
    file = create_file(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=999,
            file_id=file.id,
            source=ReceiptSource.GMAIL,
        )

    db_session.rollback()


def test_receipt_requires_existing_file(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=document.id,
            file_id=999,
            source=ReceiptSource.GMAIL,
        )

    db_session.rollback()

def test_manual_receipt_records_uploader(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file = create_file(db_session)

    user = User(
        full_name="Employe Test",
        email="employe.receipt@example.com",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    receipt = repository.create(
        document_id=document.id,
        file_id=file.id,
        source=ReceiptSource.MANUAL,
        uploaded_by_user_id=user.id,
    )

    assert receipt.uploaded_by_user_id == user.id
    assert receipt.uploaded_by_user.id == user.id


def test_synced_receipt_has_no_uploader_by_default(db_session):
    repository = DocumentReceiptRepository(db_session)
    document = create_document(db_session)
    file = create_file(db_session)

    receipt = repository.create(
        document_id=document.id,
        file_id=file.id,
        source=ReceiptSource.GMAIL,
    )

    assert receipt.uploaded_by_user_id is None
