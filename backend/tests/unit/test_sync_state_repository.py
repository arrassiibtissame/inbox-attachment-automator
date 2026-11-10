import pytest
from sqlalchemy.exc import IntegrityError
from backend.database.models.sync_account import SyncAccount
from backend.database.repositories.sync_state_repository import (
    SyncStateRepository,
)


def create_sync_account(db_session):
    account = SyncAccount(email="cabinet@gmail.com")
    db_session.add(account)
    db_session.flush()
    return account


def test_create_sync_state(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)

    state = repository.create(sync_account_id=account.id)

    assert state.id is not None
    assert state.sync_account_id == account.id
    assert state.last_history_id is None
    assert state.last_attempt_at is None
    assert state.last_successful_sync_at is None
    assert state.last_error is None


def test_get_by_id(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)
    state = repository.create(sync_account_id=account.id)

    result = repository.get_by_id(state.id)

    assert result is not None
    assert result.sync_account_id == account.id


def test_get_by_account_id(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)
    state = repository.create(sync_account_id=account.id)

    result = repository.get_by_account_id(account.id)

    assert result is not None
    assert result.id == state.id


def test_update_attempt(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)
    state = repository.create(sync_account_id=account.id)

    result = repository.update_attempt(state.id)

    assert result is not None
    assert result.last_attempt_at is not None
    assert result.updated_at is not None


def test_mark_success(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)
    state = repository.create(sync_account_id=account.id)

    repository.mark_error(state.id, error="Previous error")

    result = repository.mark_success(
        state.id,
        history_id="gmail-history-123",
    )

    assert result is not None
    assert result.last_history_id == "gmail-history-123"
    assert result.last_attempt_at is not None
    assert result.last_successful_sync_at is not None
    assert result.last_error is None


def test_mark_error_preserves_last_success(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)
    state = repository.create(sync_account_id=account.id)

    repository.mark_success(
        state.id,
        history_id="gmail-history-123",
    )

    previous_success = state.last_successful_sync_at

    result = repository.mark_error(
        state.id,
        error="Gmail connection failed",
    )

    assert result is not None
    assert result.last_error == "Gmail connection failed"
    assert result.last_successful_sync_at == previous_success
    assert result.last_history_id == "gmail-history-123"


def test_sync_account_relationship(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)

    state = repository.create(sync_account_id=account.id)

    assert account.sync_state is not None
    assert account.sync_state.id == state.id
    assert account.sync_state.sync_account.email == account.email


def test_sync_state_is_unique_per_account(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)

    repository.create(sync_account_id=account.id)

    with pytest.raises(IntegrityError):
        repository.create(sync_account_id=account.id)


def test_deleting_sync_account_deletes_its_state(db_session):
    account = create_sync_account(db_session)
    repository = SyncStateRepository(db_session)

    state = repository.create(sync_account_id=account.id)
    state_id = state.id

    db_session.delete(account)
    db_session.flush()

    assert repository.get_by_id(state_id) is None

