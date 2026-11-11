
from datetime import datetime, timezone

from backend.database.models import (
    Client,
    ClientEvent,
    ClientNote,
    ClientReminder,
    User,
    UserRole,
)


def create_user(db_session):
    user = User(
        full_name="Employe Test",
        email="activity.models@example.com",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client(db_session, user):
    client = Client(
        company_name="Entreprise Test",
        responsible_user_id=user.id,
    )
    db_session.add(client)
    db_session.flush()
    return client


def test_client_note_model_defaults_and_relationships(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)

    note = ClientNote(
        client_id=client.id,
        author_user_id=user.id,
        content="Relancer le client pour les pi?ces manquantes.",
    )
    db_session.add(note)
    db_session.flush()

    assert note.id is not None
    assert note.client.id == client.id
    assert note.author.id == user.id
    assert note.is_archived is False
    assert note.created_at is not None
    assert note.updated_at is not None


def test_client_reminder_model_defaults_and_relationships(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    due_at = datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc)

    reminder = ClientReminder(
        client_id=client.id,
        author_user_id=user.id,
        title="D?poser la d?claration",
        due_at=due_at,
    )
    db_session.add(reminder)
    db_session.flush()

    assert reminder.id is not None
    assert reminder.client.id == client.id
    assert reminder.author.id == user.id
    assert reminder.status == chr(192) + " faire"
    assert reminder.is_archived is False
    assert reminder.completed_at is None


def test_client_event_model_records_actor_and_payload(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)

    event = ClientEvent(
        client_id=client.id,
        actor_user_id=user.id,
        event_type="CLIENT_UPDATED",
        old_values={"phone_number": "0600000000"},
        new_values={"phone_number": "0611111111"},
        event_metadata={"source": "company_detail"},
    )
    db_session.add(event)
    db_session.flush()

    assert event.id is not None
    assert event.client.id == client.id
    assert event.actor.id == user.id
    assert event.old_values == {"phone_number": "0600000000"}
    assert event.new_values == {"phone_number": "0611111111"}
    assert event.event_metadata == {"source": "company_detail"}
    assert event.created_at is not None


def test_client_event_can_exist_without_actor(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)

    event = ClientEvent(
        client_id=client.id,
        actor_user_id=None,
        event_type="SYSTEM_EVENT",
    )
    db_session.add(event)
    db_session.flush()

    assert event.actor_user_id is None
    assert event.actor is None
