import hashlib

import pytest

from backend.database.models import (
    Client,
    ClassificationDecision,
    Document,
    DocumentClassification,
    DocumentReceipt,
    DocumentStatus,
    File,
    ReceiptSource,
    ReviewClaim,
    User,
    UserRole,
)
from backend.services.dashboard_service import DashboardService


def create_user(
    db_session,
    *,
    name="Test User",
    email="user@test.com",
    role=UserRole.EMPLOYEE,
    is_active=True,
):
    user = User(
        full_name=name,
        email=email,
        password_hash="test-password-hash",
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client(db_session, name, responsible_user):
    client = Client(
        company_name=name,
        responsible_user_id=responsible_user.id,
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_document(db_session, *, client=None, status=DocumentStatus.TO_REVIEW):
    document = Document(
        client_id=client.id if client else None,
        status=status,
        document_type="Facture",
    )
    db_session.add(document)
    db_session.flush()
    return document


def create_receipt(db_session, document, *, source, suffix):
    filename = f"{suffix}.pdf"

    file_record = File(
        original_filename=filename,
        stored_filename=f"stored_{suffix}.pdf",
        storage_path=f"storage/{suffix}.pdf",
        sha256=hashlib.sha256(suffix.encode()).hexdigest(),
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=1024,
    )
    db_session.add(file_record)
    db_session.flush()

    receipt = DocumentReceipt(
        document_id=document.id,
        file_id=file_record.id,
        source=source,
        source_message_id=f"message-{suffix}",
        source_part_id=f"part-{suffix}",
        sender="client@example.com",
    )
    db_session.add(receipt)
    db_session.flush()
    return receipt


def test_employee_sees_all_pending_but_only_own_classified_documents(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    client_a = create_client(db_session, "Company A", employee_a)
    client_b = create_client(db_session, "Company B", employee_b)

    pending_for_b = create_document(
        db_session,
        client=client_b,
        status=DocumentStatus.TO_REVIEW,
    )
    classified_for_a = create_document(
        db_session,
        client=client_a,
        status=DocumentStatus.CLASSIFIED,
    )
    create_document(
        db_session,
        client=client_b,
        status=DocumentStatus.CLASSIFIED,
    )

    create_receipt(
        db_session,
        pending_for_b,
        source=ReceiptSource.WHATSAPP,
        suffix="pending",
    )
    create_receipt(
        db_session,
        classified_for_a,
        source=ReceiptSource.GMAIL,
        suffix="classified-a",
    )

    service = DashboardService(db_session)
    statistics = service.get_statistics(employee_a)
    recent = service.get_recent_documents(employee_a)

    assert statistics["active_clients"] == 1
    assert statistics["documents_received"] == 2
    assert statistics["documents_to_review"] == 1
    assert statistics["classified_documents"] == 1
    assert statistics["gmail_received"] == 1
    assert statistics["whatsapp_received"] == 1

    assert {item["document_id"] for item in recent} == {
        pending_for_b.id,
        classified_for_a.id,
    }


def test_admin_sees_all_documents_and_clients(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    client_a = create_client(db_session, "Company A", employee_a)
    client_b = create_client(db_session, "Company B", employee_b)

    pending = create_document(
        db_session,
        client=client_b,
        status=DocumentStatus.TO_REVIEW,
    )
    classified = create_document(
        db_session,
        client=client_a,
        status=DocumentStatus.CLASSIFIED,
    )

    create_receipt(
        db_session,
        pending,
        source=ReceiptSource.GMAIL,
        suffix="admin-pending",
    )
    create_receipt(
        db_session,
        classified,
        source=ReceiptSource.WHATSAPP,
        suffix="admin-classified",
    )

    service = DashboardService(db_session)
    statistics = service.get_statistics(admin)

    assert statistics["active_clients"] == 2
    assert statistics["documents_received"] == 2
    assert statistics["documents_to_review"] == 1
    assert statistics["classified_documents"] == 1
    assert statistics["gmail_received"] == 1
    assert statistics["whatsapp_received"] == 1


def test_employee_cannot_view_employee_workload(db_session):
    employee = create_user(db_session)
    service = DashboardService(db_session)

    with pytest.raises(PermissionError):
        service.get_employee_workload(employee)


def test_admin_can_view_active_employee_workload(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="employee@test.com",
    )
    create_user(
        db_session,
        email="inactive@test.com",
        is_active=False,
    )

    client = create_client(db_session, "Company A", employee)
    create_document(
        db_session,
        client=client,
        status=DocumentStatus.TO_REVIEW,
    )
    create_document(
        db_session,
        client=client,
        status=DocumentStatus.CLASSIFIED,
    )

    service = DashboardService(db_session)
    workload = service.get_employee_workload(admin)

    assert len(workload) == 1
    assert workload[0]["employee_id"] == employee.id
    assert workload[0]["active_clients"] == 1
    assert workload[0]["documents_to_review"] == 1
    assert workload[0]["classified_documents"] == 1


def test_inactive_user_cannot_access_dashboard(db_session):
    inactive_user = create_user(
        db_session,
        is_active=False,
    )
    service = DashboardService(db_session)

    with pytest.raises(PermissionError):
        service.get_dashboard_data(inactive_user)

def test_dashboard_detects_document_without_identified_client(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="employee@test.com",
    )
    proposed_client = create_client(
        db_session,
        "Proposed Company",
        employee,
    )

    document = create_document(db_session)

    classification = DocumentClassification(
        document_id=document.id,
        proposed_client_id=proposed_client.id,
        confidence=0.92,
        decision=ClassificationDecision.PENDING,
    )
    db_session.add(classification)
    db_session.flush()

    service = DashboardService(db_session)
    result = service.get_documents_to_process(admin)

    assert len(result["unidentified"]) == 1
    assert result["unidentified"][0]["document_id"] == document.id
    assert result["unidentified"][0]["proposed_client_name"] == "Proposed Company"


def test_employee_sees_unidentified_documents_from_all_portfolios(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    client_b = create_client(
        db_session,
        "Company B",
        employee_b,
    )

    pending_document = create_document(db_session)
    classified_document = create_document(
        db_session,
        client=client_b,
        status=DocumentStatus.CLASSIFIED,
    )

    service = DashboardService(db_session)
    result = service.get_documents_to_process(employee_a)

    document_ids = {
        item["document_id"]
        for item in result["unidentified"]
    }

    assert pending_document.id in document_ids
    assert classified_document.id not in document_ids


def test_dashboard_detects_pending_classification(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="employee@test.com",
    )
    client = create_client(
        db_session,
        "Company Pending",
        employee,
    )
    document = create_document(db_session)

    classification = DocumentClassification(
        document_id=document.id,
        proposed_client_id=client.id,
        confidence=0.95,
        decision=ClassificationDecision.PENDING,
    )
    db_session.add(classification)
    db_session.flush()

    service = DashboardService(db_session)
    result = service.get_documents_to_process(admin)

    assert result["unidentified"][0]["decision"] == "PENDING"
    assert result["unidentified"][0]["proposed_client_name"] == "Company Pending"


def test_dashboard_returns_separate_pending_validation_list(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="employee@test.com",
    )
    client = create_client(
        db_session,
        "Company Validation",
        employee,
    )
    document = create_document(db_session)

    db_session.add(
        DocumentClassification(
            document_id=document.id,
            proposed_client_id=client.id,
            confidence=0.95,
            decision=ClassificationDecision.PENDING,
        )
    )
    db_session.flush()

    service = DashboardService(db_session)
    result = service.get_documents_to_process(admin)

    assert "awaiting_validation" in result
    assert len(result["awaiting_validation"]) == 1
    assert result["awaiting_validation"][0]["document_id"] == document.id


def test_dashboard_detects_overdue_documents_from_first_receipt(db_session):
    from datetime import datetime, timedelta, timezone

    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )

    document = create_document(db_session)
    receipt = create_receipt(
        db_session,
        document,
        source=ReceiptSource.GMAIL,
        suffix="overdue",
    )

    receipt.received_at = datetime.now(timezone.utc) - timedelta(hours=30)
    db_session.flush()

    service = DashboardService(db_session)
    result = service.get_documents_to_process(admin)

    assert "overdue" in result
    assert len(result["overdue"]) == 1
    assert result["overdue"][0]["document_id"] == document.id
    assert result["overdue"][0]["age_hours"] >= 30


def test_dashboard_shows_only_active_document_claims(db_session):
    from datetime import datetime, timedelta, timezone
    from backend.database.models import ReviewClaim

    admin = create_user(
        db_session,
        email="admin_claims@test.com",
        role=UserRole.ADMIN,
    )

    employee = create_user(
        db_session,
        name="Employe Responsable",
        email="employee_claims@test.com",
    )

    active_document = create_document(db_session)
    expired_document = create_document(db_session)

    now = datetime.now(timezone.utc)

    active_claim = ReviewClaim(
        document_id=active_document.id,
        user_id=employee.id,
        claimed_at=now - timedelta(minutes=10),
        expires_at=now + timedelta(minutes=20),
    )

    expired_claim = ReviewClaim(
        document_id=expired_document.id,
        user_id=employee.id,
        claimed_at=now - timedelta(hours=2),
        expires_at=now - timedelta(minutes=30),
    )

    db_session.add_all([active_claim, expired_claim])
    db_session.flush()

    service = DashboardService(db_session)
    result = service.get_documents_to_process(admin)

    assert "claimed" in result
    assert len(result["claimed"]) == 1
    assert result["claimed"][0]["document_id"] == active_document.id
    assert result["claimed"][0]["claimed_by"] == "Employe Responsable"
