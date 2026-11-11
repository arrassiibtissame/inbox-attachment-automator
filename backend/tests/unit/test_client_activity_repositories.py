from datetime import datetime, timezone

import pytest

from backend.database.models import Client, User, UserRole
from backend.database.repositories.client_note_repository import (
    ClientNoteRepository,
)
from backend.database.repositories.client_reminder_repository import (
    ClientReminderRepository,
)
from backend.database.repositories.client_event_repository import (
    ClientEventRepository,
)


def create_user(db_session, email="employee@test.com"):
    user = User(
        full_name="Employ? Test",
        email=email,
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client(db_session, user, name="Entreprise Test"):
    client = Client(
        company_name=name,
        responsible_user_id=user.id,
    )
    db_session.add(client)
    db_session.flush()
    return client


# -------------------- NOTES --------------------


def test_note_create_and_get_by_id(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientNoteRepository(db_session)

    note = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        content="  Relancer le client.  ",
    )

    result = repository.get_by_id(note.id)

    assert result is not None
    assert result.content == "Relancer le client."
    assert result.author_user_id == user.id
    assert result.client_id == client.id


def test_note_get_by_id_returns_none(db_session):
    repository = ClientNoteRepository(db_session)
    assert repository.get_by_id(999) is None


def test_note_rejects_empty_content(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientNoteRepository(db_session)

    with pytest.raises(ValueError):
        repository.create(
            client_id=client.id,
            author_user_id=user.id,
            content="   ",
        )


def test_note_list_filters_by_author_and_client(db_session):
    user_a = create_user(db_session, "a@test.com")
    user_b = create_user(db_session, "b@test.com")
    client = create_client(db_session, user_a)
    other_client = create_client(db_session, user_a, "Autre entreprise")
    repository = ClientNoteRepository(db_session)

    note_a = repository.create(
        client_id=client.id,
        author_user_id=user_a.id,
        content="Note A",
    )
    repository.create(
        client_id=client.id,
        author_user_id=user_b.id,
        content="Note B",
    )
    repository.create(
        client_id=other_client.id,
        author_user_id=user_a.id,
        content="Note autre client",
    )

    results = repository.list_by_client(
        client.id,
        author_user_id=user_a.id,
    )

    assert [note.id for note in results] == [note_a.id]


def test_note_archive_is_soft_and_hidden_by_default(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientNoteRepository(db_session)
    note = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        content="Note ? archiver",
    )

    repository.archive(note)

    assert note.is_archived is True
    assert repository.list_by_client(client.id) == []
    assert repository.list_by_client(
        client.id,
        include_archived=True,
    ) == [note]


def test_archived_note_cannot_be_updated(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientNoteRepository(db_session)
    note = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        content="Note initiale",
    )
    repository.archive(note)

    with pytest.raises(ValueError):
        repository.update_content(note, "Nouvelle note")


def test_note_update_rejects_empty_content(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientNoteRepository(db_session)
    note = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        content="Note initiale",
    )

    with pytest.raises(ValueError):
        repository.update_content(note, "  ")


# -------------------- RAPPELS --------------------


def test_reminder_create_and_get_by_id(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)
    due_at = datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc)

    reminder = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        title="  D?claration fiscale  ",
        description="  Pr?parer les documents  ",
        due_at=due_at,
    )

    result = repository.get_by_id(reminder.id)

    assert result is not None
    assert result.title == "D?claration fiscale"
    assert result.description == "Pr?parer les documents"
    assert result.status == "? faire"
    assert result.completed_at is None


def test_reminder_get_by_id_returns_none(db_session):
    repository = ClientReminderRepository(db_session)
    assert repository.get_by_id(999) is None


def test_reminder_rejects_empty_title(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)

    with pytest.raises(ValueError):
        repository.create(
            client_id=client.id,
            author_user_id=user.id,
            title=" ",
            due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
        )


def test_reminder_rejects_invalid_status(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)

    with pytest.raises(ValueError):
        repository.create(
            client_id=client.id,
            author_user_id=user.id,
            title="Rappel",
            due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
            status="Inconnu",
        )


def test_reminder_update_sets_and_clears_completed_at(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)
    reminder = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        title="Rappel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    repository.update(reminder, status="Termin?")
    assert reminder.status == "Termin?"
    assert reminder.completed_at is not None

    repository.update(reminder, status="En cours")
    assert reminder.status == "En cours"
    assert reminder.completed_at is None


def test_reminder_list_filters_by_author_status_and_archive(db_session):
    user_a = create_user(db_session, "a@test.com")
    user_b = create_user(db_session, "b@test.com")
    client = create_client(db_session, user_a)
    repository = ClientReminderRepository(db_session)
    due_at = datetime(2026, 12, 1, tzinfo=timezone.utc)

    reminder_a = repository.create(
        client_id=client.id,
        author_user_id=user_a.id,
        title="Rappel A",
        due_at=due_at,
    )
    repository.create(
        client_id=client.id,
        author_user_id=user_b.id,
        title="Rappel B",
        due_at=due_at,
    )
    archived = repository.create(
        client_id=client.id,
        author_user_id=user_a.id,
        title="Rappel archiv?",
        due_at=due_at,
    )
    repository.archive(archived)

    results = repository.list_by_client(
        client.id,
        author_user_id=user_a.id,
        status="? faire",
    )

    assert [item.id for item in results] == [reminder_a.id]


def test_reminder_archive_and_archived_update_rejection(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)
    reminder = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        title="Rappel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    repository.archive(reminder)

    assert reminder.is_archived is True
    assert repository.list_by_client(client.id) == []

    with pytest.raises(ValueError):
        repository.update(reminder, title="Modification")


def test_reminder_update_rejects_unknown_fields(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientReminderRepository(db_session)
    reminder = repository.create(
        client_id=client.id,
        author_user_id=user.id,
        title="Rappel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError):
        repository.update(reminder, author_user_id=999)


# -------------------- HISTORIQUE --------------------


def test_client_event_create_and_get_by_id(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientEventRepository(db_session)

    event = repository.create(
        client_id=client.id,
        actor_user_id=user.id,
        event_type="CLIENT_UPDATED",
        old_values={"phone": "0600000000"},
        new_values={"phone": "0611111111"},
        event_metadata={"source": "manual"},
    )

    result = repository.get_by_id(event.id)

    assert result is not None
    assert result.actor_user_id == user.id
    assert result.old_values == {"phone": "0600000000"}
    assert result.new_values == {"phone": "0611111111"}
    assert result.event_metadata == {"source": "manual"}


def test_client_event_allows_system_actor(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientEventRepository(db_session)

    event = repository.create(
        client_id=client.id,
        event_type="GMAIL_DOCUMENT_RECEIVED",
    )

    assert event.actor_user_id is None


def test_client_event_rejects_empty_event_type(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientEventRepository(db_session)

    with pytest.raises(ValueError):
        repository.create(
            client_id=client.id,
            event_type=" ",
        )


def test_client_event_list_filters_by_type_and_limit(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientEventRepository(db_session)

    first = repository.create(
        client_id=client.id,
        event_type="CLIENT_UPDATED",
    )
    repository.create(
        client_id=client.id,
        event_type="DOCUMENT_ADDED",
    )
    third = repository.create(
        client_id=client.id,
        event_type="CLIENT_UPDATED",
    )

    results = repository.list_by_client(
        client.id,
        event_type="CLIENT_UPDATED",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].id == third.id
    assert first.id != third.id


def test_client_event_list_rejects_invalid_limit(db_session):
    user = create_user(db_session)
    client = create_client(db_session, user)
    repository = ClientEventRepository(db_session)

    with pytest.raises(ValueError):
        repository.list_by_client(client.id, limit=0)


def test_client_event_list_by_actor(db_session):
    user_a = create_user(db_session, "a@test.com")
    user_b = create_user(db_session, "b@test.com")
    client = create_client(db_session, user_a)
    repository = ClientEventRepository(db_session)

    event_a = repository.create(
        client_id=client.id,
        actor_user_id=user_a.id,
        event_type="CLIENT_UPDATED",
    )
    repository.create(
        client_id=client.id,
        actor_user_id=user_b.id,
        event_type="CLIENT_UPDATED",
    )

    results = repository.list_by_actor(user_a.id)

    assert len(results) == 1
    assert results[0].id == event_a.id
