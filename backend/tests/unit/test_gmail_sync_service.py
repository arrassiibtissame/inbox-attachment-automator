
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.services import gmail_service
from backend.services.gmail_service import GmailService


@pytest.fixture
def sync_setup(db_session, monkeypatch):
    account_repo = MagicMock()
    state_repo = MagicMock()

    account = SimpleNamespace(id=1)
    state = SimpleNamespace(id=10)

    account_repo.get_by_email.return_value = account
    state_repo.get_by_account_id.return_value = state

    monkeypatch.setattr(
        gmail_service,
        "SyncAccountRepository",
        lambda session: account_repo,
    )
    monkeypatch.setattr(
        gmail_service,
        "SyncStateRepository",
        lambda session: state_repo,
    )

    api = MagicMock()
    api.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": []
    }

    service = GmailService()

    monkeypatch.setattr(
        service,
        "authenticate",
        lambda: (api, {"emailAddress": "test@example.com"}),
    )
    monkeypatch.setattr(service, "build_query", lambda: "has:attachment")

    return service, db_session, account_repo, state_repo, api


def test_sync_once_marks_success(sync_setup):
    service, session, account_repo, state_repo, api = sync_setup

    result = service.sync_once(session)

    assert result["email"] == "test@example.com"
    assert result["processed_messages"] == 0
    assert result["saved_documents"] == 0
    assert result["failed_messages"] == []

    state_repo.update_attempt.assert_called_once_with(10)
    state_repo.mark_success.assert_called_once_with(10)
    state_repo.mark_error.assert_not_called()


def test_sync_once_marks_error_when_message_fails(sync_setup, monkeypatch):
    service, session, account_repo, state_repo, api = sync_setup

    api.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "message-123"}]
    }

    def fail_processing(*args, **kwargs):
        raise ValueError("Attachment processing failed")

    monkeypatch.setattr(service, "process_message", fail_processing)

    result = service.sync_once(session)

    assert result["processed_messages"] == 0
    assert len(result["failed_messages"]) == 1
    assert result["failed_messages"][0]["message_id"] == "message-123"

    state_repo.mark_error.assert_called_once()
    state_repo.mark_success.assert_not_called()


def test_sync_once_marks_error_when_gmail_api_fails(sync_setup):
    service, session, account_repo, state_repo, api = sync_setup

    api.users.return_value.messages.return_value.list.return_value.execute.side_effect = (
        RuntimeError("Gmail API unavailable")
    )

    with pytest.raises(RuntimeError, match="Gmail API unavailable"):
        service.sync_once(session)

    state_repo.mark_error.assert_called_once()
    state_repo.mark_success.assert_not_called()
