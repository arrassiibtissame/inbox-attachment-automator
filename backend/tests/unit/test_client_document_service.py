from datetime import date

import pytest

from backend.database.models.client import Client
from backend.database.models.document import Document, DocumentStatus
from backend.database.models.document_receipt import (
    DocumentReceipt,
    ReceiptSource,
)
from backend.database.models.file import File
from backend.database.models.user import User, UserRole
from backend.services.client_document_service import ClientDocumentService


def create_user(db_session, email, role=UserRole.EMPLOYEE):
    user = User(
        full_name=email.split("@")[0],
        email=email,
        password_hash="test-hash",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client(db_session, responsible_user):
    client = Client(
        internal_code="CLI-001",
        company_name="Entreprise Test",
        responsible_user_id=responsible_user.id,
        is_active=True,
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_document_with_receipt(
    db_session,
    client,
    filename,
    *,
    category=None,
    status=DocumentStatus.CLASSIFIED,
    uploader=None,
    source=ReceiptSource.MANUAL,
):
    file_record = File(
        original_filename=filename,
        stored_filename=f"stored-{filename}",
        storage_path=f"documents/{filename}",
        sha256=(str(abs(hash(filename))).zfill(64))[-64:],
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=1024,
    )
    db_session.add(file_record)
    db_session.flush()

    document = Document(
        client_id=client.id,
        document_type="Facture",
        category=category,
        document_number="FAC-001",
        document_date=date(2026, 1, 15),
        status=status,
    )
    db_session.add(document)
    db_session.flush()

    receipt = DocumentReceipt(
        document_id=document.id,
        file_id=file_record.id,
        uploaded_by_user_id=uploader.id if uploader else None,
        source=source,
        sender="cabinet@example.com",
    )
    db_session.add(receipt)
    db_session.flush()

    return document, file_record, receipt


def test_lists_client_documents_with_receipt_and_uploader(db_session):
    employee = create_user(db_session, "employee@example.com")
    client = create_client(db_session, employee)
    create_document_with_receipt(
        db_session,
        client,
        "facture.pdf",
        category="Comptabilité",
        uploader=employee,
    )

    result = ClientDocumentService(db_session).list_client_documents(
        employee,
        client.id,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["name"] == "facture.pdf"
    assert item["client"] == "Entreprise Test"
    assert item["category"] == "Comptabilité"
    assert item["uploaded_by"] == employee.full_name
    assert item["source"] == "MANUAL"
    assert item["status"] == "CLASSIFIED"


def test_employee_cannot_access_another_employee_client(db_session):
    employee_a = create_user(db_session, "a@example.com")
    employee_b = create_user(db_session, "b@example.com")
    client = create_client(db_session, employee_b)

    service = ClientDocumentService(db_session)

    with pytest.raises(PermissionError):
        service.list_client_documents(employee_a, client.id)


def test_admin_can_access_employee_client(db_session):
    employee = create_user(db_session, "employee2@example.com")
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    client = create_client(db_session, employee)

    create_document_with_receipt(
        db_session,
        client,
        "contrat.pdf",
        category="Juridique",
    )

    result = ClientDocumentService(db_session).list_client_documents(
        admin,
        client.id,
    )

    assert result["total"] == 1
    assert result["items"][0]["name"] == "contrat.pdf"


def test_search_filters_filename_case_insensitively(db_session):
    employee = create_user(db_session, "search@example.com")
    client = create_client(db_session, employee)

    create_document_with_receipt(db_session, client, "Facture_Janvier.pdf")
    create_document_with_receipt(db_session, client, "Contrat.pdf")

    result = ClientDocumentService(db_session).list_client_documents(
        employee,
        client.id,
        search="facture",
    )

    assert result["total"] == 1
    assert result["items"][0]["name"] == "Facture_Janvier.pdf"


def test_category_filter_supports_unclassified_documents(db_session):
    employee = create_user(db_session, "category@example.com")
    client = create_client(db_session, employee)

    create_document_with_receipt(
        db_session,
        client,
        "sans-categorie.pdf",
        category=None,
    )
    create_document_with_receipt(
        db_session,
        client,
        "juridique.pdf",
        category="Juridique",
    )

    result = ClientDocumentService(db_session).list_client_documents(
        employee,
        client.id,
        category="Non classés",
    )

    assert result["total"] == 1
    assert result["items"][0]["name"] == "sans-categorie.pdf"


def test_status_filter_accepts_enum_value(db_session):
    employee = create_user(db_session, "status@example.com")
    client = create_client(db_session, employee)

    create_document_with_receipt(
        db_session,
        client,
        "a-verifier.pdf",
        status=DocumentStatus.TO_REVIEW,
    )
    create_document_with_receipt(
        db_session,
        client,
        "classe.pdf",
        status=DocumentStatus.CLASSIFIED,
    )

    result = ClientDocumentService(db_session).list_client_documents(
        employee,
        client.id,
        status="TO_REVIEW",
    )

    assert result["total"] == 1
    assert result["items"][0]["name"] == "a-verifier.pdf"


def test_pagination_counts_receipts_not_only_documents(db_session):
    employee = create_user(db_session, "pagination@example.com")
    client = create_client(db_session, employee)

    document, file_record, _ = create_document_with_receipt(
        db_session,
        client,
        "original.pdf",
    )

    second_file = File(
        original_filename="copie-recue.pdf",
        stored_filename="stored-copie-recue.pdf",
        storage_path="documents/copie-recue.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=2048,
    )
    db_session.add(second_file)
    db_session.flush()

    db_session.add(
        DocumentReceipt(
            document_id=document.id,
            file_id=second_file.id,
            source=ReceiptSource.WHATSAPP,
            sender="client@example.com",
        )
    )
    db_session.flush()

    service = ClientDocumentService(db_session)
    first_page = service.list_client_documents(
        employee,
        client.id,
        page=1,
        page_size=1,
    )
    second_page = service.list_client_documents(
        employee,
        client.id,
        page=2,
        page_size=1,
    )

    assert first_page["total"] == 2
    assert first_page["total_pages"] == 2
    assert len(first_page["items"]) == 1
    assert len(second_page["items"]) == 1
    assert first_page["items"][0]["receipt_id"] != second_page["items"][0]["receipt_id"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"category": "Invalide"},
        {"status": "INCONNU"},
    ],
)
def test_rejects_invalid_filters_and_pagination(db_session, kwargs):
    employee = create_user(db_session, "invalid@example.com")
    client = create_client(db_session, employee)

    with pytest.raises(ValueError):
        ClientDocumentService(db_session).list_client_documents(
            employee,
            client.id,
            **kwargs,
        )


def test_inactive_user_cannot_access_client_documents(db_session):
    employee = create_user(db_session, "inactive@example.com")
    client = create_client(db_session, employee)
    employee.is_active = False
    db_session.flush()

    with pytest.raises(PermissionError):
        ClientDocumentService(db_session).list_client_documents(
            employee,
            client.id,
        )
