import pytest

from backend.database.models.client import Client
from backend.database.models.client_event import ClientEvent
from backend.database.models.document import Document, DocumentStatus
from backend.database.models.document_classification import (
    ClassificationDecision,
)
from backend.database.models.document_event import DocumentEvent
from backend.database.models.user import User, UserRole
from backend.database.repositories.document_classification_repository import (
    DocumentClassificationRepository,
)
from backend.services.document_validation_service import (
    DocumentValidationService,
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


def make_client(session, employee, name="Client test"):
    client = Client(
        company_name=name,
        responsible_user_id=employee.id,
        is_active=True,
    )
    session.add(client)
    session.flush()
    return client


def make_document(session):
    document = Document()
    session.add(document)
    session.flush()
    return document


def make_classification(session, document, client):
    return DocumentClassificationRepository(session).create(
        document_id=document.id,
        proposed_client_id=client.id if client else None,
        confidence=0.95,
        rationale="Proposition de test",
    )


def test_validate_accepts_matching_proposal_and_creates_both_histories(
    db_session,
):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)
    classification = make_classification(db_session, document, client)

    result = DocumentValidationService(db_session).validate_document(
        user,
        document.id,
        client.id,
        category="Juridique",
        classification_id=classification.id,
    )

    assert result.client_id == client.id
    assert result.status == DocumentStatus.CLASSIFIED
    assert result.category == "Juridique"
    assert classification.decision == ClassificationDecision.ACCEPTED
    assert classification.reviewer_id == user.id
    assert classification.reviewed_at is not None

    document_events = db_session.query(DocumentEvent).filter_by(
        document_id=document.id
    ).all()
    client_events = db_session.query(ClientEvent).filter_by(
        client_id=client.id
    ).all()

    assert any(
        event.event_type == "DOCUMENT_VALIDATED"
        for event in document_events
    )
    assert any(
        event.event_type == "DOCUMENT_CLASSIFIED"
        for event in client_events
    )


def test_validate_corrects_different_proposed_client(db_session):
    user = make_user(db_session, "reviewer@test.com")
    proposed_client = make_client(
        db_session, user, "Client proposé"
    )
    selected_client = make_client(
        db_session, user, "Client correct"
    )
    document = make_document(db_session)
    classification = make_classification(
        db_session, document, proposed_client
    )

    DocumentValidationService(db_session).validate_document(
        user,
        document.id,
        selected_client.id,
        category="Comptabilité",
        classification_id=classification.id,
    )

    assert document.client_id == selected_client.id
    assert classification.decision == ClassificationDecision.CORRECTED


def test_manual_assignment_does_not_create_fake_classification(
    db_session,
):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)

    DocumentValidationService(db_session).validate_document(
        user,
        document.id,
        client.id,
        category="Non classés",
    )

    assert document.client_id == client.id
    assert document.status == DocumentStatus.CLASSIFIED
    assert document.category is None

    classifications = DocumentClassificationRepository(
        db_session
    ).list_by_document(document.id)

    assert classifications == []


def test_reject_classification_keeps_document_unassigned(db_session):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)
    classification = make_classification(db_session, document, client)

    result = DocumentValidationService(db_session).reject_classification(
        user,
        classification.id,
    )

    assert result.decision == ClassificationDecision.REJECTED
    assert result.reviewer_id == user.id
    assert document.client_id is None
    assert document.status == DocumentStatus.TO_REVIEW

    events = db_session.query(DocumentEvent).filter_by(
        document_id=document.id
    ).all()

    assert any(
        event.event_type == "CLASSIFICATION_REJECTED"
        for event in events
    )

    assert db_session.query(ClientEvent).filter_by(
        client_id=client.id
    ).count() == 0


def test_employee_cannot_assign_document_to_another_employee_client(
    db_session,
):
    employee = make_user(db_session, "employee@test.com")
    other_employee = make_user(db_session, "other@test.com")
    other_client = make_client(db_session, other_employee)
    document = make_document(db_session)

    with pytest.raises(PermissionError):
        DocumentValidationService(db_session).validate_document(
            employee,
            document.id,
            other_client.id,
        )

    assert document.client_id is None
    assert document.status == DocumentStatus.TO_REVIEW


def test_cannot_validate_document_twice(db_session):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)

    service = DocumentValidationService(db_session)

    service.validate_document(
        user,
        document.id,
        client.id,
    )

    with pytest.raises(ValueError, match="plus en attente"):
        service.validate_document(
            user,
            document.id,
            client.id,
        )


def test_cannot_use_classification_from_another_document(db_session):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)
    another_document = make_document(db_session)
    classification = make_classification(
        db_session, another_document, client
    )

    with pytest.raises(ValueError, match="ne correspond pas"):
        DocumentValidationService(db_session).validate_document(
            user,
            document.id,
            client.id,
            classification_id=classification.id,
        )

    assert document.client_id is None
    assert document.status == DocumentStatus.TO_REVIEW


def test_cannot_reject_classification_twice(db_session):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)
    classification = make_classification(db_session, document, client)

    service = DocumentValidationService(db_session)
    service.reject_classification(user, classification.id)

    with pytest.raises(ValueError, match="déjà été examinée"):
        service.reject_classification(user, classification.id)


def test_invalid_category_is_rejected_without_assigning_document(
    db_session,
):
    user = make_user(db_session, "reviewer@test.com")
    client = make_client(db_session, user)
    document = make_document(db_session)

    with pytest.raises(ValueError, match="invalide"):
        DocumentValidationService(db_session).validate_document(
            user,
            document.id,
            client.id,
            category="Catégorie inconnue",
        )

    assert document.client_id is None
    assert document.status == DocumentStatus.TO_REVIEW
