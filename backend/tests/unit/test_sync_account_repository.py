
from datetime import datetime, timezone

from backend.database.models.sync_account import SyncAccount, SyncProvider
from backend.database.repositories.sync_account_repository import (
    SyncAccountRepository,
)


def test_create_sync_account(db_session):
    repository = SyncAccountRepository(db_session)

    account = repository.create(email="cabinet@gmail.com")

    assert account.id is not None
    assert account.email == "cabinet@gmail.com"
    assert account.provider == SyncProvider.GMAIL
    assert account.is_active is True
    assert account.connected_at is None


def test_create_inactive_sync_account(db_session):
    repository = SyncAccountRepository(db_session)

    account = repository.create(
        email="cabinet@gmail.com",
        is_active=False,
    )

    assert account.is_active is False


def test_get_by_id(db_session):
    repository = SyncAccountRepository(db_session)
    account = repository.create(email="cabinet@gmail.com")

    result = repository.get_by_id(account.id)

    assert result is not None
    assert result.email == "cabinet@gmail.com"


def test_get_by_email(db_session):
    repository = SyncAccountRepository(db_session)
    account = repository.create(email="cabinet@gmail.com")

    result = repository.get_by_email("cabinet@gmail.com")

    assert result is not None
    assert result.id == account.id


def test_list_all(db_session):
    repository = SyncAccountRepository(db_session)

    repository.create(email="first@gmail.com")
    repository.create(email="second@gmail.com")

    results = repository.list_all()

    assert len(results) == 2
    assert {account.email for account in results} == {
        "first@gmail.com",
        "second@gmail.com",
    }


def test_get_active(db_session):
    repository = SyncAccountRepository(db_session)

    repository.create(
        email="inactive@gmail.com",
        is_active=False,
    )
    active_account = repository.create(email="active@gmail.com")

    result = repository.get_active()

    assert result is not None
    assert result.id == active_account.id


def test_update_status(db_session):
    repository = SyncAccountRepository(db_session)
    account = repository.create(email="cabinet@gmail.com")

    result = repository.update_status(
        account.id,
        is_active=False,
    )

    assert result is not None
    assert result.is_active is False

    result = repository.update_status(
        account.id,
        is_active=True,
    )

    assert result is not None
    assert result.is_active is True


def test_mark_connected(db_session):
    repository = SyncAccountRepository(db_session)
    account = repository.create(email="cabinet@gmail.com")

    result = repository.mark_connected(account.id)

    assert result is not None
    assert result.connected_at is not None
    assert result.updated_at is not None
    assert result.connected_at.tzinfo is not None
