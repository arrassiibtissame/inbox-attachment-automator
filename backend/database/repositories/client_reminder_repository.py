from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.client_reminder import ClientReminder


class ClientReminderRepository:
    """Database operations for client reminders."""

    ALLOWED_STATUSES = ("? faire", "En cours", "Termin?")

    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def _validate_status(cls, status: str) -> None:
        if status not in cls.ALLOWED_STATUSES:
            raise ValueError("Statut de rappel invalide.")

    def create(
        self,
        *,
        client_id: int,
        author_user_id: int,
        title: str,
        due_at: datetime,
        description: str | None = None,
        status: str = "? faire",
    ) -> ClientReminder:
        title = title.strip()
        if not title:
            raise ValueError("Le titre du rappel est obligatoire.")

        self._validate_status(status)

        reminder = ClientReminder(
            client_id=client_id,
            author_user_id=author_user_id,
            title=title,
            description=description.strip() if description else None,
            due_at=due_at,
            status=status,
            completed_at=(
                datetime.now(due_at.tzinfo)
                if status == "Termin?"
                else None
            ),
        )
        self.session.add(reminder)
        self.session.flush()
        return reminder

    def get_by_id(self, reminder_id: int) -> ClientReminder | None:
        return self.session.get(ClientReminder, reminder_id)

    def list_by_client(
        self,
        client_id: int,
        *,
        author_user_id: int | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> list[ClientReminder]:
        if status is not None:
            self._validate_status(status)

        statement = select(ClientReminder).where(
            ClientReminder.client_id == client_id
        )

        if author_user_id is not None:
            statement = statement.where(
                ClientReminder.author_user_id == author_user_id
            )

        if status is not None:
            statement = statement.where(
                ClientReminder.status == status
            )

        if not include_archived:
            statement = statement.where(
                ClientReminder.is_archived.is_(False)
            )

        statement = statement.order_by(
            ClientReminder.due_at.asc(),
            ClientReminder.id.asc(),
        )
        return list(self.session.scalars(statement).all())

    def update(
        self,
        reminder: ClientReminder,
        **changes,
    ) -> ClientReminder:
        allowed_fields = {"title", "description", "due_at", "status"}
        unknown_fields = set(changes) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"Champs de rappel non autoris?s : {', '.join(sorted(unknown_fields))}"
            )

        if reminder.is_archived:
            raise ValueError("Un rappel archiv? ne peut pas ?tre modifi?.")

        if "title" in changes:
            title = changes["title"]
            if title is None or not title.strip():
                raise ValueError("Le titre du rappel est obligatoire.")
            changes["title"] = title.strip()

        if "description" in changes:
            description = changes["description"]
            changes["description"] = (
                description.strip() or None
                if description is not None
                else None
            )

        if "status" in changes:
            self._validate_status(changes["status"])

        for field, value in changes.items():
            setattr(reminder, field, value)

        if "status" in changes:
            if changes["status"] == "Termin?":
                reminder.completed_at = datetime.now(
                    reminder.due_at.tzinfo
                )
            else:
                reminder.completed_at = None

        self.session.flush()
        return reminder

    def archive(self, reminder: ClientReminder) -> ClientReminder:
        reminder.is_archived = True
        self.session.flush()
        return reminder
