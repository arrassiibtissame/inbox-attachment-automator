
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.document_event import DocumentEvent


class DocumentEventRepository:
    """Handles database operations related to document events."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        document_id: int,
        event_type: str,
        actor_user_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        event_metadata: dict | None = None,
    ) -> DocumentEvent:
        event = DocumentEvent(
            document_id=document_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            old_values=old_values,
            new_values=new_values,
            event_metadata=event_metadata,
        )

        self.session.add(event)
        self.session.flush()

        return event

    def get_by_id(self, event_id: int) -> DocumentEvent | None:
        return self.session.get(DocumentEvent, event_id)

    def list_by_document(
        self,
        document_id: int,
    ) -> list[DocumentEvent]:
        statement = (
            select(DocumentEvent)
            .where(DocumentEvent.document_id == document_id)
            .order_by(DocumentEvent.created_at.desc(), DocumentEvent.id.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_by_actor(
        self,
        actor_user_id: int,
    ) -> list[DocumentEvent]:
        statement = (
            select(DocumentEvent)
            .where(DocumentEvent.actor_user_id == actor_user_id)
            .order_by(DocumentEvent.created_at.desc(), DocumentEvent.id.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_by_event_type(
        self,
        event_type: str,
    ) -> list[DocumentEvent]:
        statement = (
            select(DocumentEvent)
            .where(DocumentEvent.event_type == event_type)
            .order_by(DocumentEvent.created_at.desc(), DocumentEvent.id.desc())
        )

        return list(self.session.scalars(statement).all())
