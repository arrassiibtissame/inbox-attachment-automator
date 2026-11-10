
import pytest

from backend.database.models import Client, User, UserRole
from backend.database.repositories.client_repository import ClientRepository
from backend.services.client_service import ClientService


def create_user(
    db_session,
    *,
    name="Test User",
    email="user@test.com",
    role=UserRole.EMPLOYEE,
    is_active=True,
):
    user = User(
        full_name=name,
        email=email,
        password_hash="test-password-hash",
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_admin_can_see_all_clients(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    repository = ClientRepository(db_session)
    client_a = repository.create(
        company_name="Company A",
        responsible_user_id=employee_a.id,
    )
    client_b = repository.create(
        company_name="Company B",
        responsible_user_id=employee_b.id,
    )

    service = ClientService(db_session)
    clients = service.list_clients(admin)

    assert {client.id for client in clients} == {
        client_a.id,
        client_b.id,
    }


def test_employee_can_see_only_own_clients(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
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

    service = ClientService(db_session)
    clients = service.list_clients(employee_a)

    assert [client.id for client in clients] == [client_a.id]


def test_admin_can_list_active_employees(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    active_employee = create_user(
        db_session,
        email="active@test.com",
    )
    create_user(
        db_session,
        email="inactive@test.com",
        is_active=False,
    )

    service = ClientService(db_session)
    employees = service.list_available_employees(admin)

    assert [user.id for user in employees] == [active_employee.id]


def test_employee_cannot_list_available_employees(db_session):
    employee = create_user(db_session)
    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.list_available_employees(employee)


def test_admin_can_assign_client_to_active_employee(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="employee@test.com",
    )

    service = ClientService(db_session)
    client = service.create_client(
        admin,
        company_name="New Company",
        responsible_user_id=employee.id,
    )

    assert client.company_name == "New Company"
    assert client.responsible_user_id == employee.id


def test_admin_must_choose_responsible_employee(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    service = ClientService(db_session)

    with pytest.raises(ValueError):
        service.create_client(
            admin,
            company_name="New Company",
        )


def test_admin_cannot_assign_client_to_inactive_employee(db_session):
    admin = create_user(
        db_session,
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        email="inactive@test.com",
        is_active=False,
    )

    service = ClientService(db_session)

    with pytest.raises(ValueError):
        service.create_client(
            admin,
            company_name="New Company",
            responsible_user_id=employee.id,
        )


def test_employee_is_automatically_responsible_for_own_client(db_session):
    employee = create_user(db_session)
    service = ClientService(db_session)

    client = service.create_client(
        employee,
        company_name="Employee Company",
    )

    assert client.responsible_user_id == employee.id


def test_employee_cannot_assign_client_to_another_employee(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.create_client(
            employee_a,
            company_name="Company",
            responsible_user_id=employee_b.id,
        )


def test_employee_cannot_access_another_employee_client(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Private Company",
        responsible_user_id=employee_b.id,
    )

    service = ClientService(db_session)

    assert service.get_client(employee_a, client.id) is None


def test_employee_cannot_modify_another_employee_client(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Private Company",
        responsible_user_id=employee_b.id,
    )

    service = ClientService(db_session)
    result = service.update_client(
        employee_a,
        client.id,
        company_name="Modified Company",
    )

    assert result is None
    assert client.company_name == "Private Company"


def test_employee_cannot_archive_another_employee_client(db_session):
    employee_a = create_user(
        db_session,
        email="employee_a@test.com",
    )
    employee_b = create_user(
        db_session,
        email="employee_b@test.com",
    )

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Private Company",
        responsible_user_id=employee_b.id,
    )

    service = ClientService(db_session)
    result = service.archive_client(employee_a, client.id)

    assert result is None
    assert client.is_active is True


def test_archive_preserves_client_in_database(db_session):
    employee = create_user(db_session)

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Archived Company",
        responsible_user_id=employee.id,
    )

    service = ClientService(db_session)
    result = service.archive_client(employee, client.id)

    assert result is not None
    assert result.is_active is False

    archived_client = repository.get_by_id(client.id)

    assert archived_client is not None
    assert archived_client.company_name == "Archived Company"


def test_inactive_user_cannot_list_clients(db_session):
    inactive_employee = create_user(
        db_session,
        is_active=False,
    )
    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.list_clients(inactive_employee)

def test_create_client_saves_contact_name_and_email(db_session):
    employee = create_user(db_session)
    service = ClientService(db_session)

    client = service.create_client(
        employee,
        company_name="Company Contact Test",
        contact_name="Ahmed Benali",
        email="ahmed@company.com",
    )

    assert client.contact_name == "Ahmed Benali"
    assert client.email == "ahmed@company.com"


def test_update_client_modifies_contact_name_and_email(db_session):
    employee = create_user(db_session)
    service = ClientService(db_session)

    client = service.create_client(
        employee,
        company_name="Company Update Test",
        contact_name="Initial Contact",
        email="initial@company.com",
    )

    updated_client = service.update_client(
        employee,
        client.id,
        contact_name="New Contact",
        email="new@company.com",
    )

    assert updated_client is not None
    assert updated_client.contact_name == "New Contact"
    assert updated_client.email == "new@company.com"
