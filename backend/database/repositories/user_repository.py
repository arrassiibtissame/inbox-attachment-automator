
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.user import User, UserRole


class UserRepository:
    """Handles database operations related to users."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        full_name: str,
        civility: str | None = None,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role=role,
            civility=civility,
        )

        self.session.add(user)
        self.session.flush()

        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalars(statement).one_or_none()

    def list_all(
        self,
        *,
        active_only: bool = False,
    ) -> list[User]:
        statement = select(User)

        if active_only:
            statement = statement.where(User.is_active.is_(True))

        statement = statement.order_by(User.full_name)

        return list(self.session.scalars(statement).all())

    def list_by_role(
        self,
        role: UserRole,
        *,
        active_only: bool = True,
    ) -> list[User]:
        statement = select(User).where(User.role == role)

        if active_only:
            statement = statement.where(User.is_active.is_(True))

        statement = statement.order_by(User.full_name)

        return list(self.session.scalars(statement).all())

    def update_profile(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        civility: str | None = None,
        email: str | None = None,
    ) -> User | None:
        user = self.get_by_id(user_id)

        if user is None:
            return None

        if full_name is not None:
            user.full_name = full_name

        if civility is not None:
            user.civility = civility

        if email is not None:
            user.email = email

        self.session.flush()

        return user

    def set_active(
        self,
        user_id: int,
        is_active: bool,
    ) -> User | None:
        user = self.get_by_id(user_id)

        if user is None:
            return None

        user.is_active = is_active
        self.session.flush()

        return user
