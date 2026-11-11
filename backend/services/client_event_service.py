from sqlalchemy.orm import Session

from backend.database.models import User
from backend.database.repositories.client_event_repository import ClientEventRepository
from backend.services.client_service import ClientService


class ClientEventService:
    """Access-controlled client activity history."""

    def __init__(self, session: Session):
        self.client_service = ClientService(session)
        self.event_repository = ClientEventRepository(session)

    def list_events(
        self,
        current_user: User,
        client_id: int,
        *,
        event_type: str | None = None,
        limit: int | None = None,
    ):
        client = self.client_service.get_client(current_user, client_id)

        if client is None:
            raise PermissionError("Entreprise introuvable ou acc?s non autoris?.")

        return self.event_repository.list_by_client(
            client_id,
            event_type=event_type,
            limit=limit,
        )

    def create_event(
        self,
        current_user: User,
        client_id: int,
        event_type: str,
        *,
        old_values: dict | None = None,
        new_values: dict | None = None,
        event_metadata: dict | None = None,
    ):
        client = self.client_service.get_client(current_user, client_id)

        if client is None:
            raise PermissionError("Entreprise introuvable ou acc?s non autoris?.")

        return self.event_repository.create(
            client_id=client_id,
            actor_user_id=current_user.id,
            event_type=event_type,
            old_values=old_values,
            new_values=new_values,
            event_metadata=event_metadata,
        )
