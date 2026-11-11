
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.database.models.client import Client
from backend.database.models.document import Document
from backend.database.models.user import User


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
        legal_form: str | None = None,
        business_sector: str | None = None,
        incorporation_date=None,
        tax_regime: str | None = None,
        collaboration_start_date=None,
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
            legal_form=legal_form,
            business_sector=business_sector,
            incorporation_date=incorporation_date,
            tax_regime=tax_regime,
            collaboration_start_date=collaboration_start_date,
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

    def list_page(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
        responsible_user_id: int | None = None,
        status: str = "active",
        document_filter: str = "all",
        search: str = "",
    ) -> tuple[list[tuple[Client, int]], int]:
        """Return a filtered client page and the total matching count."""

        if page < 1:
            raise ValueError("La page doit etre superieure ou egale a 1.")

        if not 1 <= page_size <= 100:
            raise ValueError("La taille de page doit etre comprise entre 1 et 100.")

        if status not in {"active", "archived", "all"}:
            raise ValueError("Statut de client invalide.")

        if document_filter not in {"all", "with_documents", "without_documents"}:
            raise ValueError("Filtre de documents invalide.")

        conditions = []

        if responsible_user_id is not None:
            conditions.append(
                Client.responsible_user_id == responsible_user_id
            )

        if status == "active":
            conditions.append(Client.is_active.is_(True))
        elif status == "archived":
            conditions.append(Client.is_active.is_(False))

        document_exists = (
            select(Document.id)
            .where(Document.client_id == Client.id)
            .exists()
        )

        if document_filter == "with_documents":
            conditions.append(document_exists)
        elif document_filter == "without_documents":
            conditions.append(~document_exists)

        search = search.strip()
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Client.company_name.ilike(pattern),
                    Client.internal_code.ilike(pattern),
                    Client.ice.ilike(pattern),
                    Client.if_number.ilike(pattern),
                    Client.cnss_number.ilike(pattern),
                    Client.rc_number.ilike(pattern),
                    Client.patente.ilike(pattern),
                    Client.address.ilike(pattern),
                    Client.contact_name.ilike(pattern),
                    Client.email.ilike(pattern),
                    Client.phone_number.ilike(pattern),
                    Client.responsible_user.has(
                        User.full_name.ilike(pattern)
                    ),
                )
            )

        document_count = (
            select(func.count(Document.id))
            .where(Document.client_id == Client.id)
            .correlate(Client)
            .scalar_subquery()
        )

        total = self.session.scalar(
            select(func.count(Client.id)).where(*conditions)
        ) or 0

        statement = (
            select(Client, document_count.label("document_count"))
            .options(joinedload(Client.responsible_user))
            .where(*conditions)
            .order_by(Client.company_name, Client.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = self.session.execute(statement).all()

        results = [
            (client, int(count))
            for client, count in rows
        ]

        return results, total

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
            "legal_form",
            "business_sector",
            "incorporation_date",
            "tax_regime",
            "collaboration_start_date",
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
