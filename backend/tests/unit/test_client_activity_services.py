from datetime import datetime, timezone

import pytest

from backend.database.models import Client, User, UserRole
from backend.services.client_note_service import ClientNoteService
from backend.services.client_reminder_service import ClientReminderService
from backend.services.client_event_service import ClientEventService


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
        company_name="Entreprise Test",
        responsible_user_id=responsible_user.id,
    )
    db_session.add(client)
    db_session.flush()
    return client


def test_employee_sees_only_own_notes(db_session):
    employee_a = create_user(db_session, "a@test.com")
    employee_b = create_user(db_session, "b@test.com")
    client = create_client(db_session, employee_a)

    service_a = ClientNoteService(db_session)
    service_b = ClientNoteService(db_session)

    note_a = service_a.create_note(employee_a, client.id, "Note A")

    # B n'a pas acc?s au portefeuille de A.
    with pytest.raises(PermissionError):
        service_b.list_notes(employee_b, client.id)

    # L'administrateur peut consulter les notes des deux auteurs.
    admin = create_user(db_session, "admin@test.com", UserRole.ADMIN)
    note_b = service_a.create_note(admin, client.id, "Note admin")

    notes = service_a.list_notes(admin, client.id)
    assert {note.id for note in notes} == {note_a.id, note_b.id}


def test_admin_can_read_but_cannot_edit_employee_note(db_session):
    employee = create_user(db_session, "employee@test.com")
    admin = create_user(db_session, "admin@test.com", UserRole.ADMIN)
    client = create_client(db_session, employee)

    service = ClientNoteService(db_session)
    note = service.create_note(employee, client.id, "Note priv?e")

    assert service.get_note(admin, client.id, note.id).content == "Note priv?e"

    with pytest.raises(PermissionError):
        service.update_note(admin, client.id, note.id, "Modification")

    with pytest.raises(PermissionError):
        service.archive_note(admin, client.id, note.id)


def test_note_owner_can_update_and_archive(db_session):
    employee = create_user(db_session, "employee@test.com")
    client = create_client(db_session, employee)
    service = ClientNoteService(db_session)

    note = service.create_note(employee, client.id, "Initial")
    service.update_note(employee, client.id, note.id, "Modifi?e")
    assert note.content == "Modifi?e"

    service.archive_note(employee, client.id, note.id)
    assert service.get_note(employee, client.id, note.id) is None
    assert service.get_note(
        employee, client.id, note.id, include_archived=True
    ).is_archived is True


def test_note_cannot_be_read_through_another_client_id(db_session):
    employee = create_user(db_session, "employee@test.com")
    client_a = create_client(db_session, employee)
    client_b = create_client(db_session, employee)
    service = ClientNoteService(db_session)

    note = service.create_note(employee, client_a.id, "Note A")

    assert service.get_note(employee, client_b.id, note.id) is None


def test_employee_sees_only_own_reminders(db_session):
    employee = create_user(db_session, "employee@test.com")
    admin = create_user(db_session, "admin@test.com", UserRole.ADMIN)
    client = create_client(db_session, employee)
    service = ClientReminderService(db_session)

    reminder = service.create_reminder(
        employee,
        client.id,
        title="D?claration",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    assert len(service.list_reminders(employee, client.id)) == 1
    assert len(service.list_reminders(admin, client.id)) == 1
    assert service.get_reminder(admin, client.id, reminder.id).id == reminder.id


def test_admin_cannot_edit_or_archive_employee_reminder(db_session):
    employee = create_user(db_session, "employee@test.com")
    admin = create_user(db_session, "admin@test.com", UserRole.ADMIN)
    client = create_client(db_session, employee)
    service = ClientReminderService(db_session)

    reminder = service.create_reminder(
        employee,
        client.id,
        title="Rappel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(PermissionError):
        service.update_reminder(admin, client.id, reminder.id, title="Autre")

    with pytest.raises(PermissionError):
        service.archive_reminder(admin, client.id, reminder.id)


def test_reminder_owner_can_update_status_and_archive(db_session):
    employee = create_user(db_session, "employee@test.com")
    client = create_client(db_session, employee)
    service = ClientReminderService(db_session)

    reminder = service.create_reminder(
        employee,
        client.id,
        title="Rappel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )

    service.update_reminder(
        employee, client.id, reminder.id, status="Termin\u00e9"
    )
    assert reminder.status == "Termin\u00e9"
    assert reminder.completed_at is not None

    service.archive_reminder(employee, client.id, reminder.id)
    assert service.get_reminder(employee, client.id, reminder.id) is None


def test_event_service_checks_client_access_and_records_actor(db_session):
    employee = create_user(db_session, "employee@test.com")
    other_employee = create_user(db_session, "other@test.com")
    client = create_client(db_session, employee)

    service = ClientEventService(db_session)
    event = service.create_event(
        employee,
        client.id,
        "TEST_EVENT",
        event_metadata={"source": "unit_test"},
    )

    assert event.actor_user_id == employee.id
    assert service.list_events(employee, client.id)[0].id == event.id

    with pytest.raises(PermissionError):
        service.list_events(other_employee, client.id)


def test_note_and_reminder_actions_create_history_events(db_session):
    employee = create_user(db_session, "employee@test.com")
    client = create_client(db_session, employee)

    note_service = ClientNoteService(db_session)
    reminder_service = ClientReminderService(db_session)
    event_service = ClientEventService(db_session)

    note = note_service.create_note(employee, client.id, "Texte confidentiel")
    reminder = reminder_service.create_reminder(
        employee,
        client.id,
        title="Rappel confidentiel",
        due_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
        description="Description priv?e",
    )

    events = event_service.list_events(employee, client.id)
    event_types = {event.event_type for event in events}

    assert "NOTE_CREATED" in event_types
    assert "REMINDER_CREATED" in event_types

    # Le texte priv? ne doit jamais ?tre copi? dans l'historique.
    for event in events:
        assert "Texte confidentiel" not in str(event.event_metadata)
        assert "Description priv?e" not in str(event.event_metadata)
        assert "Rappel confidentiel" not in str(event.event_metadata)
