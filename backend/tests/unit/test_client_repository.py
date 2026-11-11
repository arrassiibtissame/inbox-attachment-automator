import pytest

from sqlalchemy import func, select

from backend.database.models import Client, Document, User, UserRole
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


def test_list_page_paginates_and_isolates_clients(db_session):
    employee_a = create_responsible_user(
        db_session,
        email="pagination_a@test.com",
    )
    employee_b = create_responsible_user(
        db_session,
        email="pagination_b@test.com",
    )

    repository = ClientRepository(db_session)

    for name in ["Company A", "Company B", "Company C"]:
        repository.create(
            company_name=name,
            responsible_user_id=employee_a.id,
        )

    repository.create(
        company_name="Private Company B",
        responsible_user_id=employee_b.id,
    )

    first_page, total = repository.list_page(
        responsible_user_id=employee_a.id,
        page=1,
        page_size=2,
        status="all",
    )
    second_page, second_total = repository.list_page(
        responsible_user_id=employee_a.id,
        page=2,
        page_size=2,
        status="all",
    )

    assert total == 3
    assert second_total == 3
    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {
        client.responsible_user_id
        for client, _ in first_page + second_page
    } == {employee_a.id}


def test_list_page_counts_real_documents_and_filters_them(db_session):
    employee = create_responsible_user(
        db_session,
        email="documents_page@test.com",
    )
    repository = ClientRepository(db_session)

    client_a = repository.create(
        company_name="Client With Two Documents",
        responsible_user_id=employee.id,
    )
    client_b = repository.create(
        company_name="Client With One Document",
        responsible_user_id=employee.id,
    )
    repository.create(
        company_name="Client Without Documents",
        responsible_user_id=employee.id,
    )

    db_session.add_all([
        Document(client_id=client_a.id),
        Document(client_id=client_a.id),
        Document(client_id=client_b.id),
    ])
    db_session.flush()

    with_documents, total_with = repository.list_page(
        responsible_user_id=employee.id,
        status="all",
        document_filter="with_documents",
    )
    without_documents, total_without = repository.list_page(
        responsible_user_id=employee.id,
        status="all",
        document_filter="without_documents",
    )

    counts = {client.id: count for client, count in with_documents}

    assert total_with == 2
    assert counts[client_a.id] == 2
    assert counts[client_b.id] == 1
    assert total_without == 1
    assert without_documents[0][0].company_name == "Client Without Documents"


def test_list_page_searches_responsible_user_name(db_session):
    employee = create_responsible_user(
        db_session,
        email="responsible_search@test.com",
    )
    employee.full_name = "Amina Responsable"
    db_session.flush()

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Alpha Company",
        responsible_user_id=employee.id,
    )
    repository.create(
        company_name="Beta Company",
        responsible_user_id=employee.id,
    )

    results, total = repository.list_page(
        status="all",
        search="Amina Responsable",
    )

    assert total == 2
    assert len(results) == 2
    assert all(
        item.responsible_user.full_name == "Amina Responsable"
        for item, _ in results
    )


def test_list_page_filters_active_and_archived_clients(db_session):
    employee = create_responsible_user(
        db_session,
        email="status_page@test.com",
    )
    repository = ClientRepository(db_session)

    active_client = repository.create(
        company_name="Active Page Client",
        responsible_user_id=employee.id,
    )
    archived_client = repository.create(
        company_name="Archived Page Client",
        responsible_user_id=employee.id,
    )
    repository.set_active(archived_client, False)

    active_results, active_total = repository.list_page(
        responsible_user_id=employee.id,
        status="active",
    )
    archived_results, archived_total = repository.list_page(
        responsible_user_id=employee.id,
        status="archived",
    )

    assert active_total == 1
    assert active_results[0][0].id == active_client.id
    assert archived_total == 1
    assert archived_results[0][0].id == archived_client.id


def test_list_page_rejects_invalid_pagination_and_filters(db_session):
    repository = ClientRepository(db_session)

    with pytest.raises(ValueError):
        repository.list_page(page=0)

    with pytest.raises(ValueError):
        repository.list_page(page_size=101)

    with pytest.raises(ValueError):
        repository.list_page(status="deleted")

    with pytest.raises(ValueError):
        repository.list_page(document_filter="pending")
