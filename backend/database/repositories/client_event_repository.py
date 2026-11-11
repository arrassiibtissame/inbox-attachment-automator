from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.client_event import ClientEvent


class ClientEventRepository:
    """Database operations for client activity history."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        client_id: int,
        event_type: str,
        actor_user_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        event_metadata: dict | None = None,
    ) -> ClientEvent:
        event_type = event_type.strip()
        if not event_type:
            raise ValueError("Le type d'?v?nement est obligatoire.")

        event = ClientEvent(
            client_id=client_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            old_values=old_values,
            new_values=new_values,
            event_metadata=event_metadata,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def get_by_id(self, event_id: int) -> ClientEvent | None:
        return self.session.get(ClientEvent, event_id)

    def list_by_client(
        self,
        client_id: int,
        *,
        event_type: str | None = None,
        limit: int | None = None,
    ) -> list[ClientEvent]:
        if limit is not None and limit < 1:
            raise ValueError("La limite doit ?tre sup?rieure ? z?ro.")

        statement = select(ClientEvent).where(
            ClientEvent.client_id == client_id
        )

        if event_type is not None:
            statement = statement.where(
                ClientEvent.event_type == event_type
            )

        statement = statement.order_by(
            ClientEvent.created_at.desc(),
            ClientEvent.id.desc(),
        )

        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.scalars(statement).all())

    def list_by_actor(
        self,
        actor_user_id: int,
    ) -> list[ClientEvent]:
        statement = (
            select(ClientEvent)
            .where(ClientEvent.actor_user_id == actor_user_id)
            .order_by(
                ClientEvent.created_at.desc(),
                ClientEvent.id.desc(),
            )
        )
        return list(self.session.scalars(statement).all())
