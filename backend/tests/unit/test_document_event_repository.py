
import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models.document import Document
from backend.database.models.document_event import DocumentEvent
from backend.database.models.user import User, UserRole
from backend.database.repositories.document_event_repository import (
    DocumentEventRepository,
)


def create_user(db_session, email="actor@test.com"):
    user = User(
        full_name="Test Actor",
        email=email,
        password_hash="test_hash",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_document(db_session):
    document = Document()
    db_session.add(document)
    db_session.flush()
    return document


def test_create_event(db_session):
    repository = DocumentEventRepository(db_session)
    document = create_document(db_session)
    actor = create_user(db_session)

    event = repository.create(
        document_id=document.id,
        actor_user_id=actor.id,
        event_type="DOCUMENT_UPDATED",
        old_values={"status": "TO_REVIEW"},
        new_values={"status": "CLASSIFIED"},
        event_metadata={"source": "manual"},
    )

    assert event.id is not None
    assert event.document_id == document.id
    assert event.actor_user_id == actor.id
    assert event.event_type == "DOCUMENT_UPDATED"
    assert event.old_values == {"status": "TO_REVIEW"}
    assert event.new_values == {"status": "CLASSIFIED"}
    assert event.event_metadata == {"source": "manual"}


def test_create_automatic_event_without_actor(db_session):
    repository = DocumentEventRepository(db_session)
    document = create_document(db_session)

    event = repository.create(
        document_id=document.id,
        event_type="AI_CLASSIFICATION_PROPOSED",
    )

    assert event.id is not None
    assert event.actor_user_id is None


def test_get_by_id(db_session):
    repository = DocumentEventRepository(db_session)
    document = create_document(db_session)

    event = repository.create(
        document_id=document.id,
        event_type="DOCUMENT_RECEIVED",
    )

    result = repository.get_by_id(event.id)

    assert result is not None
    assert result.id == event.id


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = DocumentEventRepository(db_session)

    assert repository.get_by_id(999) is None


def test_list_by_document(db_session):
    repository = DocumentEventRepository(db_session)

    document_one = create_document(db_session)
    document_two = create_document(db_session)

    first = repository.create(
        document_id=document_one.id,
        event_type="DOCUMENT_RECEIVED",
    )
    second = repository.create(
        document_id=document_one.id,
        event_type="DOCUMENT_UPDATED",
    )

    repository.create(
        document_id=document_two.id,
        event_type="DOCUMENT_RECEIVED",
    )

    results = repository.list_by_document(document_one.id)

    assert len(results) == 2
    assert {event.id for event in results} == {first.id, second.id}


def test_list_by_actor(db_session):
    repository = DocumentEventRepository(db_session)
    document = create_document(db_session)

    actor_one = create_user(db_session, "actor1@test.com")
    actor_two = create_user(db_session, "actor2@test.com")

    first = repository.create(
        document_id=document.id,
        actor_user_id=actor_one.id,
        event_type="DOCUMENT_UPDATED",
    )

    repository.create(
        document_id=document.id,
        actor_user_id=actor_two.id,
        event_type="DOCUMENT_UPDATED",
    )

    results = repository.list_by_actor(actor_one.id)

    assert len(results) == 1
    assert results[0].id == first.id


def test_list_by_event_type(db_session):
    repository = DocumentEventRepository(db_session)
    document = create_document(db_session)

    first = repository.create(
        document_id=document.id,
        event_type="DOCUMENT_RECEIVED",
    )

    repository.create(
        document_id=document.id,
        event_type="DOCUMENT_UPDATED",
    )

    results = repository.list_by_event_type("DOCUMENT_RECEIVED")

    assert len(results) == 1
    assert results[0].id == first.id


def test_event_requires_existing_document(db_session):
    repository = DocumentEventRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=999,
            event_type="DOCUMENT_RECEIVED",
        )

    db_session.rollback()
