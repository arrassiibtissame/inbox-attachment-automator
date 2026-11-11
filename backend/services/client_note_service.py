from sqlalchemy.orm import Session

from backend.database.models import User, UserRole
from backend.database.repositories.client_note_repository import ClientNoteRepository
from backend.database.repositories.client_event_repository import ClientEventRepository
from backend.services.client_service import ClientService


class ClientNoteService:
    """Business rules and permissions for private client notes."""

    def __init__(self, session: Session):
        self.client_service = ClientService(session)
        self.note_repository = ClientNoteRepository(session)
        self.event_repository = ClientEventRepository(session)

    def _require_client(self, current_user: User, client_id: int):
        client = self.client_service.get_client(current_user, client_id)
        if client is None:
            raise PermissionError("Entreprise introuvable ou acc?s non autoris?.")
        return client

    @staticmethod
    def _can_read(note, current_user: User) -> bool:
        return (
            current_user.role == UserRole.ADMIN
            or note.author_user_id == current_user.id
        )

    def list_notes(
        self,
        current_user: User,
        client_id: int,
        *,
        include_archived: bool = False,
    ):
        self._require_client(current_user, client_id)

        author_id = (
            None
            if current_user.role == UserRole.ADMIN
            else current_user.id
        )

        return self.note_repository.list_by_client(
            client_id,
            author_user_id=author_id,
            include_archived=include_archived,
        )

    def get_note(
        self,
        current_user: User,
        client_id: int,
        note_id: int,
        *,
        include_archived: bool = False,
    ):
        self._require_client(current_user, client_id)
        note = self.note_repository.get_by_id(note_id)

        if note is None or note.client_id != client_id:
            return None
        if note.is_archived and not include_archived:
            return None
        if not self._can_read(note, current_user):
            return None

        return note

    def create_note(
        self,
        current_user: User,
        client_id: int,
        content: str,
    ):
        self._require_client(current_user, client_id)

        note = self.note_repository.create(
            client_id=client_id,
            author_user_id=current_user.id,
            content=content,
        )

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="NOTE_CREATED",
            event_metadata={"note_id": note.id},
        )
        return note

    def update_note(
        self,
        current_user: User,
        client_id: int,
        note_id: int,
        content: str,
    ):
        self._require_client(current_user, client_id)
        note = self.note_repository.get_by_id(note_id)

        if (
            note is None
            or note.client_id != client_id
            or note.author_user_id != current_user.id
        ):
            raise PermissionError("Vous ne pouvez pas modifier cette note.")

        updated = self.note_repository.update_content(note, content)

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="NOTE_UPDATED",
            event_metadata={"note_id": note.id},
        )
        return updated

    def archive_note(
        self,
        current_user: User,
        client_id: int,
        note_id: int,
    ):
        self._require_client(current_user, client_id)
        note = self.note_repository.get_by_id(note_id)

        if (
            note is None
            or note.client_id != client_id
            or note.author_user_id != current_user.id
        ):
            raise PermissionError("Vous ne pouvez pas archiver cette note.")

        if note.is_archived:
            return note

        archived = self.note_repository.archive(note)

        self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type="NOTE_ARCHIVED",
            event_metadata={"note_id": note.id},
        )
        return archived
