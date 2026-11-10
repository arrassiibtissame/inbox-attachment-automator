
from sqlalchemy import func, select

from backend.database.models import Client, User, UserRole
from backend.database.repositories.client_repository import ClientRepository


def create_responsible_user(db_session, email="employee@test.com"):
    """Creates a user responsible for managing clients."""

    user = User(
        full_name="Test Employee",
        email=email,
        password_hash="test-password-hash",
        role=UserRole.EMPLOYEE,
    )

    db_session.add(user)
    db_session.flush()

    return user


def test_get_by_id(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    client = repository.create(
        company_name="Company A",
        responsible_user_id=user.id,
        internal_code="CLI-001",
    )

    result = repository.get_by_id(client.id)

    assert result is not None
    assert result.company_name == "Company A"
    assert result.internal_code == "CLI-001"


def test_get_by_ice(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    client = repository.create(
        company_name="Company B",
        responsible_user_id=user.id,
        ice="001234567000089",
    )

    result = repository.get_by_ice("001234567000089")

    assert result is not None
    assert result.id == client.id


def test_get_by_internal_code(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    client = repository.create(
        company_name="Company C",
        responsible_user_id=user.id,
        internal_code="CLI-003",
    )

    result = repository.get_by_internal_code("CLI-003")

    assert result is not None
    assert result.id == client.id


def test_list_by_if_number_returns_multiple_clients(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    repository.create(
        company_name="Company Alpha",
        responsible_user_id=user.id,
        if_number="12345678",
    )

    repository.create(
        company_name="Company Beta",
        responsible_user_id=user.id,
        if_number="12345678",
    )

    results = repository.list_by_if_number("12345678")

    assert len(results) == 2
    assert [client.company_name for client in results] == [
        "Company Alpha",
        "Company Beta",
    ]


def test_list_by_responsible_user_filters_inactive_clients(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    active_client = repository.create(
        company_name="Active Company",
        responsible_user_id=user.id,
    )

    inactive_client = repository.create(
        company_name="Inactive Company",
        responsible_user_id=user.id,
    )

    inactive_client.is_active = False
    db_session.flush()

    active_results = repository.list_by_responsible_user(user.id)

    all_results = repository.list_by_responsible_user(
        user.id,
        active_only=False,
    )

    assert [client.id for client in active_results] == [
        active_client.id
    ]

    assert len(all_results) == 2


def test_rollback_removes_uncommitted_user_and_client(db_session):
    user = create_responsible_user(
        db_session,
        email="rollback@test.com",
    )

    repository = ClientRepository(db_session)

    repository.create(
        company_name="Temporary Company",
        responsible_user_id=user.id,
        internal_code="ROLLBACK-001",
    )

    # Undo all uncommitted changes.
    db_session.rollback()

    # Verify the database after rollback.
    user_count = db_session.scalar(
        select(func.count()).select_from(User)
    )

    client_count = db_session.scalar(
        select(func.count()).select_from(Client)
    )

    assert user_count == 0
    assert client_count == 0

def test_clients_are_isolated_by_responsible_user(db_session):
    employee_a = create_responsible_user(
        db_session,
        email="employee_a@test.com",
    )

    employee_b = create_responsible_user(
        db_session,
        email="employee_b@test.com",
    )

    repository = ClientRepository(db_session)

    client_a = repository.create(
        company_name="Company A",
        responsible_user_id=employee_a.id,
    )

    repository.create(
        company_name="Company B",
        responsible_user_id=employee_b.id,
    )

    employee_a_clients = repository.list_by_responsible_user(
        employee_a.id
    )

    employee_b_clients = repository.list_by_responsible_user(
        employee_b.id
    )

    assert [client.id for client in employee_a_clients] == [
        client_a.id
    ]

    assert len(employee_b_clients) == 1
    assert employee_b_clients[0].company_name == "Company B"


def test_user_and_client_relationships(db_session):
    user = create_responsible_user(db_session)
    repository = ClientRepository(db_session)

    client = repository.create(
        company_name="Relationship Company",
        responsible_user_id=user.id,
    )

    db_session.flush()

    assert client.responsible_user.id == user.id
    assert client.responsible_user.email == user.email

    assert len(user.managed_clients) == 1
    assert client in user.managed_clients
