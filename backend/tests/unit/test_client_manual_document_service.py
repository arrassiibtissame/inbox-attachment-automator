import hashlib

import pytest

from backend.database.models.client import Client
from backend.database.models.document import DocumentStatus
from backend.database.models.document_event import DocumentEvent
from backend.database.models.document_receipt import (
    DocumentReceipt,
    ReceiptSource,
)
from backend.database.models.user import User, UserRole
from backend.services.client_manual_document_service import (
    ClientManualDocumentService,
)


def make_user(session, email, role=UserRole.EMPLOYEE):
    user = User(
        full_name=email.split("@")[0],
        email=email,
        password_hash="test-hash",
        role=role,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def make_client(session, employee):
    client = Client(
        internal_code="MANUAL-001",
        company_name="Client Manuel",
        responsible_user_id=employee.id,
        is_active=True,
    )
    session.add(client)
    session.flush()
    return client


def test_add_manual_document_creates_file_document_receipt_and_event(
    db_session, tmp_path, monkeypatch
):
    from backend.services import client_manual_document_service as module

    monkeypatch.setattr(module.settings, "STORAGE_DIR", tmp_path)

    user = make_user(db_session, "manual@example.com")
    client = make_client(db_session, user)
    content = b"%PDF-1.7\nmanual test document"

    document = ClientManualDocumentService(
        db_session
    ).add_manual_document(
        user,
        client.id,
        filename="contrat.pdf",
        content=content,
        category="Juridique",
    )

    receipt = db_session.query(DocumentReceipt).filter_by(
        document_id=document.id
    ).one()

    assert document.client_id == client.id
    assert document.category == "Juridique"
    assert document.status == DocumentStatus.TO_REVIEW
    assert receipt.source == ReceiptSource.MANUAL
    assert receipt.uploaded_by_user_id == user.id
    assert receipt.file.original_filename == "contrat.pdf"
    assert receipt.file.sha256 == hashlib.sha256(content).hexdigest()
    assert receipt.file.size_bytes == len(content)
    assert (tmp_path / receipt.file.storage_path.split(
        str(tmp_path)
    )[-1].lstrip("\\/")).is_file()

    event = db_session.query(DocumentEvent).filter_by(
        document_id=document.id,
        event_type="DOCUMENT_MANUALLY_ADDED",
    ).one()
    assert event.actor_user_id == user.id


def test_duplicate_file_for_same_client_is_rejected(
    db_session, tmp_path, monkeypatch
):
    from backend.services import client_manual_document_service as module

    monkeypatch.setattr(module.settings, "STORAGE_DIR", tmp_path)

    user = make_user(db_session, "duplicate@example.com")
    client = make_client(db_session, user)
    service = ClientManualDocumentService(db_session)
    content = b"%PDF-1.7\nsame document"

    service.add_manual_document(
        user, client.id, filename="same.pdf", content=content
    )

    with pytest.raises(ValueError, match="d?j? associ?"):
        service.add_manual_document(
            user, client.id, filename="same.pdf", content=content
        )


def test_same_file_can_be_attached_to_another_client(
    db_session, tmp_path, monkeypatch
):
    from backend.services import client_manual_document_service as module

    monkeypatch.setattr(module.settings, "STORAGE_DIR", tmp_path)

    user_a = make_user(db_session, "portfolio-a@example.com")
    user_b = make_user(db_session, "portfolio-b@example.com")
    client_a = make_client(db_session, user_a)
    client_b = Client(
        internal_code="MANUAL-002",
        company_name="Second Client",
        responsible_user_id=user_b.id,
        is_active=True,
    )
    db_session.add(client_b)
    db_session.flush()

    content = b"%PDF-1.7\nshared physical file"
    service = ClientManualDocumentService(db_session)

    doc_a = service.add_manual_document(
        user_a, client_a.id, filename="piece.pdf", content=content
    )
    doc_b = service.add_manual_document(
        user_b, client_b.id, filename="piece.pdf", content=content
    )

    receipt_a = db_session.query(DocumentReceipt).filter_by(
        document_id=doc_a.id
    ).one()
    receipt_b = db_session.query(DocumentReceipt).filter_by(
        document_id=doc_b.id
    ).one()

    assert doc_a.id != doc_b.id
    assert receipt_a.file_id == receipt_b.file_id


def test_employee_cannot_add_document_to_another_portfolio(
    db_session, tmp_path, monkeypatch
):
    from backend.services import client_manual_document_service as module

    monkeypatch.setattr(module.settings, "STORAGE_DIR", tmp_path)

    owner = make_user(db_session, "owner-manual@example.com")
    other = make_user(db_session, "other-manual@example.com")
    client = make_client(db_session, owner)

    with pytest.raises(PermissionError):
        ClientManualDocumentService(db_session).add_manual_document(
            other,
            client.id,
            filename="secret.pdf",
            content=b"%PDF-1.7\nprivate",
        )

    assert list(tmp_path.rglob("*")) == []


@pytest.mark.parametrize(
    "filename,content",
    [
        ("script.exe", b"not allowed"),
        ("empty.pdf", b""),
        ("invalid.pdf", b"not a pdf"),
    ],
)
def test_rejects_invalid_manual_files(
    db_session, tmp_path, monkeypatch, filename, content
):
    from backend.services import client_manual_document_service as module

    monkeypatch.setattr(module.settings, "STORAGE_DIR", tmp_path)

    user = make_user(db_session, f"invalid-{filename}@example.com")
    client = make_client(db_session, user)

    with pytest.raises(ValueError):
        ClientManualDocumentService(db_session).add_manual_document(
            user,
            client.id,
            filename=filename,
            content=content,
        )

    assert list(tmp_path.rglob("*")) == []


def test_update_category_records_old_and_new_values(db_session):
    user = make_user(db_session, "category-change@example.com")
    client = make_client(db_session, user)

    from backend.database.models.document import Document

    document = Document(
        client_id=client.id,
        category="Juridique",
        status=DocumentStatus.TO_REVIEW,
    )
    db_session.add(document)
    db_session.flush()

    updated = ClientManualDocumentService(
        db_session
    ).update_document_category(
        user,
        client.id,
        document.id,
        "Fiscalité",
    )

    event = db_session.query(DocumentEvent).filter_by(
        document_id=document.id,
        event_type="DOCUMENT_CATEGORY_CHANGED",
    ).one()

    assert updated.category == "Fiscalité"
    assert event.old_values == {"category": "Juridique"}
    assert event.new_values == {"category": "Fiscalité"}
    assert event.actor_user_id == user.id


def test_cannot_change_category_of_another_client_document(db_session):
    owner = make_user(db_session, "category-owner@example.com")
    other = make_user(db_session, "category-other@example.com")
    client = make_client(db_session, owner)

    from backend.database.models.document import Document

    document = Document(
        client_id=client.id,
        status=DocumentStatus.TO_REVIEW,
    )
    db_session.add(document)
    db_session.flush()

    with pytest.raises(PermissionError):
        ClientManualDocumentService(db_session).update_document_category(
            other,
            client.id,
            document.id,
            "Social",
        )
