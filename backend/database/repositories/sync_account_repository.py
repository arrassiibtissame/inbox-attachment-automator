
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.sync_account import SyncAccount, SyncProvider


class SyncAccountRepository:
    """Handles Gmail synchronization accounts."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        email: str,
        provider: SyncProvider = SyncProvider.GMAIL,
        is_active: bool = True,
    ) -> SyncAccount:
        account = SyncAccount(
            email=email,
            provider=provider,
            is_active=is_active,
        )

        self.session.add(account)
        self.session.flush()

        return account

    def get_by_id(self, account_id: int) -> SyncAccount | None:
        statement = select(SyncAccount).where(
            SyncAccount.id == account_id
        )

        return self.session.scalars(statement).one_or_none()

    def get_by_email(self, email: str) -> SyncAccount | None:
        statement = select(SyncAccount).where(
            SyncAccount.email == email
        )

        return self.session.scalars(statement).one_or_none()

    def list_all(self) -> list[SyncAccount]:
        statement = (
            select(SyncAccount)
            .order_by(SyncAccount.created_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def get_active(self) -> SyncAccount | None:
        statement = (
            select(SyncAccount)
            .where(SyncAccount.is_active.is_(True))
            .order_by(SyncAccount.created_at.desc())
        )

        return self.session.scalars(statement).first()

    def update_status(
        self,
        account_id: int,
        *,
        is_active: bool,
    ) -> SyncAccount | None:
        account = self.get_by_id(account_id)

        if account is None:
            return None

        account.is_active = is_active
        account.updated_at = datetime.now(timezone.utc)

        self.session.flush()

        return account

    def mark_connected(
        self,
        account_id: int,
    ) -> SyncAccount | None:
        account = self.get_by_id(account_id)

        if account is None:
            return None

        account.connected_at = datetime.now(timezone.utc)
        account.updated_at = datetime.now(timezone.utc)

        self.session.flush()

        return account
