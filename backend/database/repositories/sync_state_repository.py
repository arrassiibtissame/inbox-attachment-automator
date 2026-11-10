
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.sync_state import SyncState


class SyncStateRepository:
    """Handles Gmail synchronization state."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        sync_account_id: int,
    ) -> SyncState:
        state = SyncState(
            sync_account_id=sync_account_id,
        )

        self.session.add(state)
        self.session.flush()

        return state

    def get_by_id(self, state_id: int) -> SyncState | None:
        statement = select(SyncState).where(
            SyncState.id == state_id
        )

        return self.session.scalars(statement).one_or_none()

    def get_by_account_id(
        self,
        sync_account_id: int,
    ) -> SyncState | None:
        statement = select(SyncState).where(
            SyncState.sync_account_id == sync_account_id
        )

        return self.session.scalars(statement).one_or_none()

    def update_attempt(
        self,
        state_id: int,
    ) -> SyncState | None:
        state = self.get_by_id(state_id)

        if state is None:
            return None

        state.last_attempt_at = datetime.now(timezone.utc)
        state.updated_at = datetime.now(timezone.utc)

        self.session.flush()

        return state

    def mark_success(
        self,
        state_id: int,
        *,
        history_id: str | None = None,
    ) -> SyncState | None:
        state = self.get_by_id(state_id)

        if state is None:
            return None

        now = datetime.now(timezone.utc)

        state.last_history_id = history_id
        state.last_attempt_at = now
        state.last_successful_sync_at = now
        state.last_error = None
        state.updated_at = now

        self.session.flush()

        return state

    def mark_error(
        self,
        state_id: int,
        *,
        error: str,
    ) -> SyncState | None:
        state = self.get_by_id(state_id)

        if state is None:
            return None

        state.last_attempt_at = datetime.now(timezone.utc)
        state.last_error = error
        state.updated_at = datetime.now(timezone.utc)

        self.session.flush()

        return state
