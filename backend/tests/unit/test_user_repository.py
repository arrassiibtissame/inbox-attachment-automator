
from sqlalchemy import func, select

from backend.database.models import User, UserRole
from backend.database.repositories.user_repository import UserRepository


def test_create_employee(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Test Employee",
        email="employee@test.com",
        password_hash="hashed-password",
    )

    assert user.id is not None
    assert user.full_name == "Test Employee"
    assert user.email == "employee@test.com"
    assert user.password_hash == "hashed-password"
    assert user.role == UserRole.EMPLOYEE
    assert user.is_active is True


def test_create_admin(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Test Admin",
        email="admin@test.com",
        password_hash="hashed-password",
        role=UserRole.ADMIN,
    )

    assert user.role == UserRole.ADMIN


def test_get_by_id(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Employee One",
        email="one@test.com",
        password_hash="hashed-password",
    )

    result = repository.get_by_id(user.id)

    assert result is not None
    assert result.email == "one@test.com"


def test_get_by_email(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Employee Two",
        email="two@test.com",
        password_hash="hashed-password",
    )

    result = repository.get_by_email("two@test.com")

    assert result is not None
    assert result.id == user.id


def test_get_by_email_returns_none_when_not_found(db_session):
    repository = UserRepository(db_session)

    result = repository.get_by_email("unknown@test.com")

    assert result is None


def test_list_all_users(db_session):
    repository = UserRepository(db_session)

    repository.create(
        full_name="Alice",
        email="alice@test.com",
        password_hash="hash-1",
    )

    repository.create(
        full_name="Bob",
        email="bob@test.com",
        password_hash="hash-2",
    )

    results = repository.list_all()

    assert len(results) == 2
    assert [user.full_name for user in results] == ["Alice", "Bob"]


def test_list_all_active_users_only(db_session):
    repository = UserRepository(db_session)

    active_user = repository.create(
        full_name="Active Employee",
        email="active@test.com",
        password_hash="hash-1",
    )

    inactive_user = repository.create(
        full_name="Inactive Employee",
        email="inactive@test.com",
        password_hash="hash-2",
    )

    repository.set_active(inactive_user.id, False)

    results = repository.list_all(active_only=True)

    assert [user.id for user in results] == [active_user.id]


def test_list_by_role(db_session):
    repository = UserRepository(db_session)

    repository.create(
        full_name="Admin User",
        email="admin@test.com",
        password_hash="hash-1",
        role=UserRole.ADMIN,
    )

    repository.create(
        full_name="Employee User",
        email="employee@test.com",
        password_hash="hash-2",
        role=UserRole.EMPLOYEE,
    )

    results = repository.list_by_role(UserRole.EMPLOYEE)

    assert len(results) == 1
    assert results[0].role == UserRole.EMPLOYEE


def test_update_profile(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Old Name",
        email="old@test.com",
        password_hash="hashed-password",
    )

    updated_user = repository.update_profile(
        user.id,
        full_name="New Name",
        email="new@test.com",
    )

    assert updated_user is not None
    assert updated_user.full_name == "New Name"
    assert updated_user.email == "new@test.com"


def test_update_profile_returns_none_when_not_found(db_session):
    repository = UserRepository(db_session)

    result = repository.update_profile(
        999,
        full_name="Unknown User",
    )

    assert result is None


def test_set_active(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        full_name="Employee",
        email="employee@test.com",
        password_hash="hashed-password",
    )

    result = repository.set_active(user.id, False)

    assert result is not None
    assert result.is_active is False


def test_set_active_returns_none_when_not_found(db_session):
    repository = UserRepository(db_session)

    result = repository.set_active(999, False)

    assert result is None


def test_rollback_removes_uncommitted_user(db_session):
    repository = UserRepository(db_session)

    repository.create(
        full_name="Temporary User",
        email="temporary@test.com",
        password_hash="hashed-password",
    )

    db_session.rollback()

    user_count = db_session.scalar(
        select(func.count()).select_from(User)
    )

    assert user_count == 0
