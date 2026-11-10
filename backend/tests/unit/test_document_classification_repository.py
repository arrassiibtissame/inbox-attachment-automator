
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models.client import Client
from backend.database.models.document import Document
from backend.database.models.document_classification import (
    ClassificationDecision,
    DocumentClassification,
)
from backend.database.models.user import User, UserRole
from backend.database.repositories.document_classification_repository import (
    DocumentClassificationRepository,
)


def create_user(db_session, email="reviewer@test.com"):
    user = User(
        full_name="Test Reviewer",
        email=email,
        password_hash="test_hash",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client(db_session, responsible_user):
    client = Client(
        company_name="Test Company",
        responsible_user_id=responsible_user.id,
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_document(db_session):
    document = Document()
    db_session.add(document)
    db_session.flush()
    return document


def test_create_classification(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)

    classification = repository.create(
        document_id=document.id,
        proposed_client_id=None,
        confidence=0.95,
        extracted_data={"invoice_number": "FAC-001"},
        rationale="Company information detected.",
    )

    assert classification.id is not None
    assert classification.document_id == document.id
    assert classification.confidence == 0.95
    assert classification.extracted_data == {"invoice_number": "FAC-001"}
    assert classification.decision == ClassificationDecision.PENDING
    assert classification.reviewer_id is None
    assert classification.reviewed_at is None


def test_get_by_id(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)

    classification = repository.create(document_id=document.id)

    result = repository.get_by_id(classification.id)

    assert result is not None
    assert result.id == classification.id


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = DocumentClassificationRepository(db_session)

    assert repository.get_by_id(999) is None


def test_list_by_document(db_session):
    repository = DocumentClassificationRepository(db_session)

    document_one = create_document(db_session)
    document_two = create_document(db_session)

    first = repository.create(document_id=document_one.id)
    second = repository.create(document_id=document_one.id)
    repository.create(document_id=document_two.id)

    results = repository.list_by_document(document_one.id)

    assert len(results) == 2
    assert {item.id for item in results} == {first.id, second.id}


def test_list_pending(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)

    pending = repository.create(document_id=document.id)

    reviewer = create_user(db_session)
    accepted = repository.create(document_id=document.id)
    repository.record_decision(
        classification_id=accepted.id,
        decision=ClassificationDecision.ACCEPTED,
        reviewer_id=reviewer.id,
    )

    results = repository.list_pending()

    assert len(results) == 1
    assert results[0].id == pending.id


def test_list_by_decision(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = repository.create(document_id=document.id)

    repository.record_decision(
        classification_id=classification.id,
        decision=ClassificationDecision.REJECTED,
        reviewer_id=reviewer.id,
    )

    results = repository.list_by_decision(ClassificationDecision.REJECTED)

    assert len(results) == 1
    assert results[0].id == classification.id


def test_record_accepted_decision(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = repository.create(document_id=document.id)

    result = repository.record_decision(
        classification_id=classification.id,
        decision=ClassificationDecision.ACCEPTED,
        reviewer_id=reviewer.id,
    )

    assert result is not None
    assert result.decision == ClassificationDecision.ACCEPTED
    assert result.reviewer_id == reviewer.id
    assert isinstance(result.reviewed_at, datetime)
    assert result.reviewed_at.tzinfo is not None


def test_record_rejected_decision(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = repository.create(document_id=document.id)

    result = repository.record_decision(
        classification_id=classification.id,
        decision=ClassificationDecision.REJECTED,
        reviewer_id=reviewer.id,
    )

    assert result.decision == ClassificationDecision.REJECTED


def test_record_corrected_decision(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = repository.create(document_id=document.id)

    result = repository.record_decision(
        classification_id=classification.id,
        decision=ClassificationDecision.CORRECTED,
        reviewer_id=reviewer.id,
    )

    assert result.decision == ClassificationDecision.CORRECTED


def test_record_decision_returns_none_when_not_found(db_session):
    repository = DocumentClassificationRepository(db_session)
    reviewer = create_user(db_session)

    result = repository.record_decision(
        classification_id=999,
        decision=ClassificationDecision.ACCEPTED,
        reviewer_id=reviewer.id,
    )

    assert result is None


def test_record_pending_decision_is_rejected(db_session):
    repository = DocumentClassificationRepository(db_session)

    with pytest.raises(ValueError, match="cannot be PENDING"):
        repository.record_decision(
            classification_id=1,
            decision=ClassificationDecision.PENDING,
            reviewer_id=1,
        )


def test_record_decision_twice_is_rejected(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = repository.create(document_id=document.id)

    repository.record_decision(
        classification_id=classification.id,
        decision=ClassificationDecision.ACCEPTED,
        reviewer_id=reviewer.id,
    )

    with pytest.raises(ValueError, match="already been reviewed"):
        repository.record_decision(
            classification_id=classification.id,
            decision=ClassificationDecision.REJECTED,
            reviewer_id=reviewer.id,
        )


def test_classification_requires_existing_document(db_session):
    repository = DocumentClassificationRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(document_id=999)

    db_session.rollback()


def test_confidence_must_be_between_zero_and_one(db_session):
    repository = DocumentClassificationRepository(db_session)
    document = create_document(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=document.id,
            confidence=1.5,
        )

    db_session.rollback()


def test_pending_classification_cannot_have_reviewer(db_session):
    document = create_document(db_session)
    reviewer = create_user(db_session)

    classification = DocumentClassification(
        document_id=document.id,
        decision=ClassificationDecision.PENDING,
        reviewer_id=reviewer.id,
    )
    db_session.add(classification)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()
