
from sqlalchemy.orm import Session

from backend.database.models.user import User, UserRole
from backend.database.repositories.user_repository import UserRepository
from backend.services.auth_service import AuthService


class EmployeeService:
    """Handles employee management by administrators."""

    VALID_CIVILITIES = {"Monsieur", "Madame"}

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)

    def _ensure_admin(self, current_user: User) -> None:
        admin = self.user_repository.get_by_id(current_user.id)

        if (
            admin is None
            or not admin.is_active
            or admin.role != UserRole.ADMIN
        ):
            raise PermissionError(
                "Seul un administrateur actif peut gérer les employés."
            )

    @staticmethod
    def _validate_civility(civility: str) -> str:
        civility = civility.strip()

        if civility not in EmployeeService.VALID_CIVILITIES:
            raise ValueError(
                "La civilité doit être Monsieur ou Madame."
            )

        return civility

    def list_employees(self, current_user: User) -> list[User]:
        self._ensure_admin(current_user)

        return self.user_repository.list_by_role(
            UserRole.EMPLOYEE,
            active_only=False,
        )

    def create_employee(
        self,
        current_user: User,
        *,
        full_name: str,
        civility: str,
        email: str,
        password: str,
    ) -> User:
        self._ensure_admin(current_user)

        full_name = full_name.strip()
        email = email.strip().lower()

        if not full_name:
            raise ValueError("Le nom complet est obligatoire.")

        if not email:
            raise ValueError("L'adresse email est obligatoire.")

        if self.user_repository.get_by_email(email):
            raise ValueError("Cette adresse email est déjà utilisée.")

        civility = self._validate_civility(civility)
        password_hash = AuthService.hash_password(password)

        return self.user_repository.create(
            full_name=full_name,
            civility=civility,
            email=email,
            password_hash=password_hash,
            role=UserRole.EMPLOYEE,
        )

    def set_employee_active(
        self,
        current_user: User,
        employee_id: int,
        is_active: bool,
    ) -> User:
        """Activer ou désactiver un compte employé."""

        self._ensure_admin(current_user)

        employee = self.user_repository.get_by_id(employee_id)

        if employee is None or employee.role != UserRole.EMPLOYEE:
            raise ValueError("Employé introuvable.")

        updated_employee = self.user_repository.set_active(
            employee_id,
            is_active,
        )

        if updated_employee is None:
            raise ValueError("Impossible de modifier le compte employé.")

        return updated_employee

    def update_employee(
        self,
        current_user: User,
        employee_id: int,
        *,
        full_name: str | None = None,
        civility: str | None = None,
        email: str | None = None,
    ) -> User:
        self._ensure_admin(current_user)

        employee = self.user_repository.get_by_id(employee_id)

        if employee is None or employee.role != UserRole.EMPLOYEE:
            raise ValueError("Employé introuvable.")

        changes = {}

        if full_name is not None:
            full_name = full_name.strip()

            if not full_name:
                raise ValueError("Le nom complet est obligatoire.")

            changes["full_name"] = full_name

        if civility is not None:
            changes["civility"] = self._validate_civility(civility)

        if email is not None:
            email = email.strip().lower()

            if not email:
                raise ValueError("L'adresse email est obligatoire.")

            existing_user = self.user_repository.get_by_email(email)

            if existing_user and existing_user.id != employee.id:
                raise ValueError("Cette adresse email est déjà utilisée.")

            changes["email"] = email

        updated_employee = self.user_repository.update_profile(
            employee_id,
            **changes,
        )

        return updated_employee
