
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.client import Client


class ClientRepository:
    """Handles database operations related to clients."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        company_name: str,
        responsible_user_id: int,
        internal_code: str | None = None,
        ice: str | None = None,
        if_number: str | None = None,
        cnss_number: str | None = None,
        rc_number: str | None = None,
        rc_city: str | None = None,
        patente: str | None = None,
        phone_number: str | None = None,
        contact_name: str | None = None,
        email: str | None = None,
        address: str | None = None,
    ) -> Client:
        client = Client(
            company_name=company_name,
            responsible_user_id=responsible_user_id,
            internal_code=internal_code,
            ice=ice,
            if_number=if_number,
            cnss_number=cnss_number,
            rc_number=rc_number,
            rc_city=rc_city,
            patente=patente,
            phone_number=phone_number,
            contact_name=contact_name,
            email=email,
            address=address,
        )

        self.session.add(client)
        self.session.flush()

        return client

    def get_by_id(self, client_id: int) -> Client | None:
        return self.session.get(Client, client_id)

    def get_by_ice(self, ice: str) -> Client | None:
        statement = select(Client).where(Client.ice == ice)
        return self.session.scalars(statement).one_or_none()

    def get_by_internal_code(self, internal_code: str) -> Client | None:
        statement = select(Client).where(
            Client.internal_code == internal_code
        )
        return self.session.scalars(statement).one_or_none()

    def list_by_if_number(self, if_number: str) -> list[Client]:
        statement = (
            select(Client)
            .where(Client.if_number == if_number)
            .order_by(Client.company_name)
        )
        return list(self.session.scalars(statement).all())

    def list_by_responsible_user(
        self,
        user_id: int,
        *,
        active_only: bool = True,
    ) -> list[Client]:
        statement = select(Client).where(
            Client.responsible_user_id == user_id
        )

        if active_only:
            statement = statement.where(Client.is_active.is_(True))

        statement = statement.order_by(Client.company_name)

        return list(self.session.scalars(statement).all())

    def list_all(
        self,
        *,
        active_only: bool = True,
    ) -> list[Client]:
        """List all clients, mainly for administrators."""
        statement = select(Client)

        if active_only:
            statement = statement.where(Client.is_active.is_(True))

        statement = statement.order_by(Client.company_name)

        return list(self.session.scalars(statement).all())

    def update(
        self,
        client: Client,
        **changes,
    ) -> Client:
        """Update allowed client fields."""
        allowed_fields = {
            "company_name",
            "internal_code",
            "ice",
            "if_number",
            "cnss_number",
            "rc_number",
            "rc_city",
            "patente",
            "phone_number",
            "contact_name",
            "email",
            "address",
        }

        for field, value in changes.items():
            if field not in allowed_fields:
                raise ValueError(
                    f"Modification non autorisée : {field}"
                )

            setattr(client, field, value)

        self.session.flush()
        return client

    def set_active(
        self,
        client: Client,
        active: bool,
    ) -> Client:
        """Archive or restore a client."""
        client.is_active = active
        self.session.flush()
        return client
