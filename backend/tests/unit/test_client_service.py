
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

# --------------------------------------------------
# FILTRES ET REACTIVATION DES CLIENTS
# --------------------------------------------------

def test_admin_can_filter_active_archived_and_all_clients(db_session):
    admin = create_user(
        db_session,
        email="admin_status@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(db_session, email="employee_status@test.com")

    repository = ClientRepository(db_session)
    active_client = repository.create(
        company_name="Active Company",
        responsible_user_id=employee.id,
    )
    archived_client = repository.create(
        company_name="Archived Company",
        responsible_user_id=employee.id,
    )
    repository.set_active(archived_client, False)

    service = ClientService(db_session)

    assert [c.id for c in service.list_clients(admin, status="active")] == [
        active_client.id
    ]
    assert [c.id for c in service.list_clients(admin, status="archived")] == [
        archived_client.id
    ]
    assert {c.id for c in service.list_clients(admin, status="all")} == {
        active_client.id,
        archived_client.id,
    }


def test_employee_can_list_only_own_archived_clients(db_session):
    employee_a = create_user(db_session, email="employee_a_archived@test.com")
    employee_b = create_user(db_session, email="employee_b_archived@test.com")

    repository = ClientRepository(db_session)
    own_client = repository.create(
        company_name="Own Archived Company",
        responsible_user_id=employee_a.id,
    )
    other_client = repository.create(
        company_name="Other Archived Company",
        responsible_user_id=employee_b.id,
    )
    repository.set_active(own_client, False)
    repository.set_active(other_client, False)

    service = ClientService(db_session)
    clients = service.list_clients(employee_a, status="archived")

    assert [client.id for client in clients] == [own_client.id]


def test_list_clients_rejects_unknown_status(db_session):
    employee = create_user(db_session)
    service = ClientService(db_session)

    with pytest.raises(ValueError):
        service.list_clients(employee, status="deleted")


def test_employee_can_restore_own_archived_client(db_session):
    employee = create_user(db_session)
    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Company To Restore",
        responsible_user_id=employee.id,
        internal_code="RESTORE-01",
    )
    repository.set_active(client, False)

    service = ClientService(db_session)
    restored = service.restore_client(employee, client.id)

    assert restored is not None
    assert restored.is_active is True
    assert restored.company_name == "Company To Restore"
    assert restored.internal_code == "RESTORE-01"
    assert restored.responsible_user_id == employee.id


def test_employee_cannot_restore_another_employee_archived_client(db_session):
    employee_a = create_user(db_session, email="restore_a@test.com")
    employee_b = create_user(db_session, email="restore_b@test.com")

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Private Archived Company",
        responsible_user_id=employee_b.id,
    )
    repository.set_active(client, False)

    service = ClientService(db_session)
    result = service.restore_client(employee_a, client.id)

    assert result is None
    assert client.is_active is False


def test_admin_can_restore_any_archived_client(db_session):
    admin = create_user(
        db_session,
        email="admin_restore@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(db_session, email="employee_restore@test.com")

    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Employee Archived Company",
        responsible_user_id=employee.id,
    )
    repository.set_active(client, False)

    service = ClientService(db_session)
    restored = service.restore_client(admin, client.id)

    assert restored is not None
    assert restored.is_active is True
    assert restored.responsible_user_id == employee.id


def test_restoring_active_client_is_idempotent(db_session):
    employee = create_user(db_session)
    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Already Active Company",
        responsible_user_id=employee.id,
    )

    service = ClientService(db_session)
    result = service.restore_client(employee, client.id)

    assert result is client
    assert result.is_active is True


def test_inactive_user_cannot_restore_archived_client(db_session):
    employee = create_user(
        db_session,
        email="inactive_restore@test.com",
        is_active=False,
    )
    repository = ClientRepository(db_session)
    client = repository.create(
        company_name="Archived For Inactive User",
        responsible_user_id=employee.id,
    )
    repository.set_active(client, False)

    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.restore_client(employee, client.id)




# --------------------------------------------------
# PAGINATION SECURISEE DES CLIENTS
# --------------------------------------------------

def test_admin_can_use_paginated_client_listing(db_session):
    admin = create_user(
        db_session,
        email="admin_page@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(db_session, email="employee_page@test.com")

    repository = ClientRepository(db_session)

    for number in range(35):
        repository.create(
            company_name=f"Company {number:02d}",
            responsible_user_id=employee.id,
        )

    service = ClientService(db_session)

    first_page, total = service.list_clients_page(
        admin,
        page=1,
        page_size=30,
    )
    second_page, second_total = service.list_clients_page(
        admin,
        page=2,
        page_size=30,
    )

    assert len(first_page) == 30
    assert len(second_page) == 5
    assert total == 35
    assert second_total == 35

    first_ids = {client.id for client, count in first_page}
    second_ids = {client.id for client, count in second_page}
    assert first_ids.isdisjoint(second_ids)


def test_admin_can_filter_paginated_clients_by_employee(db_session):
    admin = create_user(
        db_session,
        email="admin_filter@test.com",
        role=UserRole.ADMIN,
    )
    employee_a = create_user(db_session, email="filter_a@test.com")
    employee_b = create_user(db_session, email="filter_b@test.com")

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
    results, total = service.list_clients_page(
        admin,
        responsible_user_id=employee_a.id,
    )

    assert total == 1
    assert [client.id for client, count in results] == [client_a.id]


def test_employee_paginated_listing_is_limited_to_own_portfolio(db_session):
    employee_a = create_user(db_session, email="page_employee_a@test.com")
    employee_b = create_user(db_session, email="page_employee_b@test.com")

    repository = ClientRepository(db_session)
    own_client = repository.create(
        company_name="Own Company",
        responsible_user_id=employee_a.id,
    )
    repository.create(
        company_name="Other Company",
        responsible_user_id=employee_b.id,
    )

    service = ClientService(db_session)
    results, total = service.list_clients_page(employee_a)

    assert total == 1
    assert [client.id for client, count in results] == [own_client.id]


def test_employee_cannot_request_another_employee_portfolio_page(db_session):
    employee_a = create_user(db_session, email="secure_a@test.com")
    employee_b = create_user(db_session, email="secure_b@test.com")

    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.list_clients_page(
            employee_a,
            responsible_user_id=employee_b.id,
        )


def test_inactive_user_cannot_use_paginated_client_listing(db_session):
    inactive_employee = create_user(
        db_session,
        email="inactive_page@test.com",
        is_active=False,
    )

    service = ClientService(db_session)

    with pytest.raises(PermissionError):
        service.list_clients_page(inactive_employee)


def test_paginated_client_listing_rejects_invalid_filters(db_session):
    employee = create_user(db_session, email="invalid_page@test.com")
    service = ClientService(db_session)

    with pytest.raises(ValueError):
        service.list_clients_page(employee, status="deleted")

    with pytest.raises(ValueError):
        service.list_clients_page(employee, document_filter="pending")

    with pytest.raises(ValueError):
        service.list_clients_page(employee, page=0)

    with pytest.raises(ValueError):
        service.list_clients_page(employee, page_size=101)
