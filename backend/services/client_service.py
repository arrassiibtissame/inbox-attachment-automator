
from sqlalchemy.orm import Session

from backend.database.models.client import Client
from backend.database.models.user import User, UserRole
from backend.database.repositories.client_repository import ClientRepository
from backend.database.repositories.user_repository import UserRepository


class ClientService:
    """Handles client business rules and access permissions."""

    def __init__(self, session: Session):
        self.client_repository = ClientRepository(session)
        self.user_repository = UserRepository(session)

    @staticmethod
    def _ensure_active_user(user: User) -> None:
        if not user.is_active:
            raise PermissionError("Cet utilisateur est désactivé.")

    @staticmethod
    def _ensure_admin(user: User) -> None:
        if user.role != UserRole.ADMIN:
            raise PermissionError(
                "Cette opération est réservée à l'administrateur."
            )

    def list_clients(
        self,
        current_user: User,
        *,
        status: str = "active",
    ) -> list[Client]:
        """List clients within the user's portfolio and requested status."""
        self._ensure_active_user(current_user)

        if status not in {"active", "archived", "all"}:
            raise ValueError(
                "Statut invalide. Valeurs autoris?es : active, archived, all."
            )

        if current_user.role == UserRole.ADMIN:
            clients = self.client_repository.list_all(active_only=False)
        elif current_user.role == UserRole.EMPLOYEE:
            clients = self.client_repository.list_by_responsible_user(
                current_user.id,
                active_only=False,
            )
        else:
            raise PermissionError("R?le utilisateur non autoris?.")

        if status == "active":
            return [client for client in clients if client.is_active]
        if status == "archived":
            return [client for client in clients if not client.is_active]
        return clients

    def list_clients_page(
        self,
        current_user: User,
        *,
        page: int = 1,
        page_size: int = 30,
        status: str = "active",
        document_filter: str = "all",
        search: str = "",
        responsible_user_id: int | None = None,
    ) -> tuple[list[tuple[Client, int]], int]:
        """List one secure page of clients within the user's permissions."""

        self._ensure_active_user(current_user)

        if status not in {"active", "archived", "all"}:
            raise ValueError("Statut de client invalide.")

        if document_filter not in {
            "all",
            "with_documents",
            "without_documents",
        }:
            raise ValueError("Filtre de documents invalide.")

        if current_user.role == UserRole.ADMIN:
            if responsible_user_id is not None:
                responsible_user = self.user_repository.get_by_id(
                    responsible_user_id
                )

                if (
                    responsible_user is None
                    or responsible_user.role != UserRole.EMPLOYEE
                ):
                    raise ValueError("Employe responsable invalide.")

            portfolio_user_id = responsible_user_id

        elif current_user.role == UserRole.EMPLOYEE:
            if (
                responsible_user_id is not None
                and responsible_user_id != current_user.id
            ):
                raise PermissionError(
                    "Un employe ne peut pas consulter un autre portefeuille."
                )

            portfolio_user_id = current_user.id

        else:
            raise PermissionError("Role utilisateur non autorise.")

        return self.client_repository.list_page(
            page=page,
            page_size=page_size,
            responsible_user_id=portfolio_user_id,
            status=status,
            document_filter=document_filter,
            search=search,
        )

    def list_available_employees(
        self,
        current_user: User,
    ) -> list[User]:
        """Return active employees for the admin assignment form."""
        self._ensure_active_user(current_user)
        self._ensure_admin(current_user)

        return self.user_repository.list_by_role(
            UserRole.EMPLOYEE,
            active_only=True,
        )

    def create_client(
        self,
        current_user: User,
        *,
        company_name: str,
        responsible_user_id: int | None = None,
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
        """Create a client with the correct portfolio assignment."""
        self._ensure_active_user(current_user)

        company_name = company_name.strip()

        if not company_name:
            raise ValueError("Le nom de l'entreprise est obligatoire.")

        if current_user.role == UserRole.ADMIN:
            if responsible_user_id is None:
                raise ValueError(
                    "L'administrateur doit choisir un employé responsable."
                )

            responsible_user = self.user_repository.get_by_id(
                responsible_user_id
            )

            if (
                responsible_user is None
                or not responsible_user.is_active
                or responsible_user.role != UserRole.EMPLOYEE
            ):
                raise ValueError(
                    "L'employé responsable est introuvable ou inactif."
                )

        elif current_user.role == UserRole.EMPLOYEE:
            if responsible_user_id is not None:
                raise PermissionError(
                    "Un employé ne peut pas choisir un autre responsable."
                )

            responsible_user_id = current_user.id

        else:
            raise PermissionError("Rôle utilisateur non autorisé.")

        return self.client_repository.create(
            company_name=company_name,
            responsible_user_id=responsible_user_id,
            internal_code=self._clean(internal_code),
            ice=self._clean(ice),
            if_number=self._clean(if_number),
            cnss_number=self._clean(cnss_number),
            rc_number=self._clean(rc_number),
            rc_city=self._clean(rc_city),
            patente=self._clean(patente),
            legal_form=self._clean(legal_form),
            business_sector=self._clean(business_sector),
            incorporation_date=incorporation_date,
            tax_regime=self._clean(tax_regime),
            collaboration_start_date=collaboration_start_date,
            phone_number=self._clean(phone_number),
            contact_name=self._clean(contact_name),
            email=self._clean(email),
            address=self._clean(address),
        )

    def get_client(
        self,
        current_user: User,
        client_id: int,
        *,
        include_archived: bool = False,
    ) -> Client | None:
        """Return a client only if the current user has portfolio access."""
        self._ensure_active_user(current_user)

        client = self.client_repository.get_by_id(client_id)
        if client is None:
            return None

        if current_user.role == UserRole.ADMIN:
            pass
        elif (
            current_user.role == UserRole.EMPLOYEE
            and client.responsible_user_id == current_user.id
        ):
            pass
        else:
            return None

        if not include_archived and not client.is_active:
            return None

        return client

    def update_client(
        self,
        current_user: User,
        client_id: int,
        **changes,
    ) -> Client | None:
        """Update an accessible active client."""
        client = self.get_client(current_user, client_id)

        if client is None:
            return None

        if "responsible_user_id" in changes:
            raise ValueError(
                "Le changement de responsable sera géré séparément."
            )

        if "company_name" in changes:
            name = changes["company_name"]

            if name is None or not name.strip():
                raise ValueError(
                    "Le nom de l'entreprise est obligatoire."
                )

            changes["company_name"] = name.strip()

        optional_fields = {
            "internal_code",
            "ice",
            "if_number",
            "cnss_number",
            "rc_number",
            "rc_city",
            "patente",
            "legal_form",
            "business_sector",
            "tax_regime",
            "phone_number",
            "contact_name",
            "email",
            "address",
        }

        for field in optional_fields.intersection(changes):
            changes[field] = self._clean(changes[field])

        return self.client_repository.update(client, **changes)

    def archive_client(
        self,
        current_user: User,
        client_id: int,
    ) -> Client | None:
        """Archive an active client without deleting its data."""
        client = self.get_client(current_user, client_id)
        if client is None:
            return None
        return self.client_repository.set_active(client, False)

    def restore_client(
        self,
        current_user: User,
        client_id: int,
    ) -> Client | None:
        """Restore an archived client without changing its portfolio."""
        client = self.get_client(
            current_user,
            client_id,
            include_archived=True,
        )
        if client is None:
            return None
        if client.is_active:
            return client
        return self.client_repository.set_active(client, True)

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None
