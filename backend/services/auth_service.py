
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from backend.database.models.user import User
from backend.database.repositories.user_repository import UserRepository


class AuthService:
    """Handles user authentication and password security."""

    password_hasher = PasswordHash.recommended()

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password using the recommended Argon2 configuration."""
        if not password or not password.strip():
            raise ValueError("Le mot de passe ne peut pas être vide.")

        return cls.password_hasher.hash(password)

    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """Verify a password against its stored hash."""
        if not password or not password_hash:
            return False

        try:
            return cls.password_hasher.verify(password, password_hash)
        except (ValueError, TypeError):
            return False

    def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate an active user by email and password."""
        if not email or not password:
            return None

        user = self.user_repository.get_by_email(email.strip().lower())

        if user is None or not user.is_active:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user
