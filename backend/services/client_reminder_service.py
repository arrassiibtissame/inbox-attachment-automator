from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.models import User, UserRole
from backend.database.repositories.client_reminder_repository import ClientReminderRepository
from backend.database.repositories.client_event_repository import ClientEventRepository
from backend.services.client_service import ClientService


class ClientReminderService:
    """Business rules and permissions for private client reminders."""

    def __init__(self, session: Session):
        self.client_service = ClientService(session)
        self.reminder_repository = ClientReminderRepository(session)
        self.event_repository = ClientEventRepository(session)

    def _require_client(self, current_user: User, client_id: int):
        client = self.client_service.get_client(current_user, client_id)
        if client is None:
            raise PermissionError("Entreprise introuvable ou acc?s non autoris?.")
        return client

    @staticmethod
    def _can_read(reminder, current_user: User) -> bool:
        return (
            current_user.role == UserRole.ADMIN
            or reminder.author_user_id == current_user.id
        )

    def list_reminders(
        self,
        current_user: User,
        client_id: int,
        *,
        status: str | None = None,
        include_archived: bool = False,
    ):
        self._require_client(current_user, client_id)

        author_id = (
            None
            if current_user.role == UserRole.ADMIN
            else current_user.id
        )

        return self.reminder_repository.list_by_client(
            client_id,
            author_user_id=author_id,
            status=status,
            include_archived=include_archived,
        )

    def get_reminder(
        self,
        current_user: User,
        client_id: int,
        reminder_id: int,
        *,
        include_archived: bool = False,
    ):
        self._require_client(current_user, client_id)
        reminder = self.reminder_repository.get_by_id(reminder_id)

        if reminder is None or reminder.client_id != client_id:
            return None
        if reminder.is_archived and not include_archived:
            return None
        if not self._can_read(reminder, current_user):
            return None

        return reminder

    def create_reminder(
        self,
        current_user: User,
        client_id: int,
        *,
        title: str,
        due_at: datetime,
        description: str | None = None,
        status: str = "\u00c0 faire",
    ):
        self._require_client(current_user, client_id)

        reminder = self.reminder_repository.create(
            client_id=client_id,
            author_user_id=current_user.id,
            title=title,
            due_at=due_at,
            description=description,
            status=status,
        )

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="REMINDER_CREATED",
            event_metadata={"reminder_id": reminder.id},
        )
        return reminder

    def update_reminder(
        self,
        current_user: User,
        client_id: int,
        reminder_id: int,
        **changes,
    ):
        self._require_client(current_user, client_id)
        reminder = self.reminder_repository.get_by_id(reminder_id)

        if (
            reminder is None
            or reminder.client_id != client_id
            or reminder.author_user_id != current_user.id
        ):
            raise PermissionError("Vous ne pouvez pas modifier ce rappel.")

        updated = self.reminder_repository.update(reminder, **changes)

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="REMINDER_UPDATED",
            event_metadata={
                "reminder_id": reminder.id,
                "changed_fields": sorted(changes.keys()),
            },
        )
        return updated

    def archive_reminder(
        self,
        current_user: User,
        client_id: int,
        reminder_id: int,
    ):
        self._require_client(current_user, client_id)
        reminder = self.reminder_repository.get_by_id(reminder_id)

        if (
            reminder is None
            or reminder.client_id != client_id
            or reminder.author_user_id != current_user.id
        ):
            raise PermissionError("Vous ne pouvez pas archiver ce rappel.")

        if reminder.is_archived:
            return reminder

        archived = self.reminder_repository.archive(reminder)

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="REMINDER_ARCHIVED",
            event_metadata={"reminder_id": reminder.id},
        )
        return archived
