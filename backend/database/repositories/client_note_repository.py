from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.client_note import ClientNote


class ClientNoteRepository:
    """Database operations for client notes."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        client_id: int,
        author_user_id: int,
        content: str,
    ) -> ClientNote:
        content = content.strip()
        if not content:
            raise ValueError("Le contenu de la note est obligatoire.")

        note = ClientNote(
            client_id=client_id,
            author_user_id=author_user_id,
            content=content,
        )
        self.session.add(note)
        self.session.flush()
        return note

    def get_by_id(self, note_id: int) -> ClientNote | None:
        return self.session.get(ClientNote, note_id)

    def list_by_client(
        self,
        client_id: int,
        *,
        author_user_id: int | None = None,
        include_archived: bool = False,
    ) -> list[ClientNote]:
        statement = select(ClientNote).where(
            ClientNote.client_id == client_id
        )

        if author_user_id is not None:
            statement = statement.where(
                ClientNote.author_user_id == author_user_id
            )

        if not include_archived:
            statement = statement.where(
                ClientNote.is_archived.is_(False)
            )

        statement = statement.order_by(
            ClientNote.created_at.desc(),
            ClientNote.id.desc(),
        )
        return list(self.session.scalars(statement).all())

    def update_content(
        self,
        note: ClientNote,
        content: str,
    ) -> ClientNote:
        content = content.strip()
        if not content:
            raise ValueError("Le contenu de la note est obligatoire.")

        if note.is_archived:
            raise ValueError("Une note archiv?e ne peut pas ?tre modifi?e.")

        note.content = content
        self.session.flush()
        return note

    def archive(self, note: ClientNote) -> ClientNote:
        note.is_archived = True
        self.session.flush()
        return note
