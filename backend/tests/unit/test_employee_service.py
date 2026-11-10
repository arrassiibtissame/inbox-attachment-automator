
import pytest

from backend.database.models.user import User, UserRole
from backend.services.auth_service import AuthService
from backend.services.employee_service import EmployeeService


def create_user(
    db_session,
    *,
    name,
    email,
    role=UserRole.EMPLOYEE,
    is_active=True,
    civility=None,
):
    user = User(
        full_name=name,
        email=email,
        password_hash="test-password-hash",
        role=role,
        is_active=is_active,
        civility=civility,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_admin_can_list_employees(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        name="Employé",
        email="employee@test.com",
    )

    service = EmployeeService(db_session)

    employees = service.list_employees(admin)

    assert len(employees) == 1
    assert employees[0].id == employee.id


def test_admin_can_list_inactive_employees(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        name="Employé",
        email="employee@test.com",
        is_active=False,
    )

    service = EmployeeService(db_session)

    employees = service.list_employees(admin)

    assert any(item.id == employee.id for item in employees)


def test_employee_cannot_list_employees(db_session):
    employee = create_user(
        db_session,
        name="Employé",
        email="employee@test.com",
    )

    service = EmployeeService(db_session)

    with pytest.raises(PermissionError):
        service.list_employees(employee)


def test_inactive_admin_cannot_list_employees(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=False,
    )

    service = EmployeeService(db_session)

    with pytest.raises(PermissionError):
        service.list_employees(admin)


def test_admin_can_create_employee(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )

    service = EmployeeService(db_session)

    employee = service.create_employee(
        admin,
        full_name="  Sara Exemple  ",
        civility="Madame",
        email=" SARA@TEST.COM ",
        password="StrongPassword123!",
    )

    assert employee.full_name == "Sara Exemple"
    assert employee.email == "sara@test.com"
    assert employee.civility == "Madame"
    assert employee.role == UserRole.EMPLOYEE
    assert employee.password_hash != "StrongPassword123!"
    assert AuthService.verify_password(
        "StrongPassword123!",
        employee.password_hash,
    )


def test_employee_cannot_create_another_employee(db_session):
    employee = create_user(
        db_session,
        name="Employé",
        email="employee@test.com",
    )

    service = EmployeeService(db_session)

    with pytest.raises(PermissionError):
        service.create_employee(
            employee,
            full_name="Nouvel employé",
            civility="Monsieur",
            email="new@test.com",
            password="StrongPassword123!",
        )


def test_create_employee_rejects_invalid_civility(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )

    service = EmployeeService(db_session)

    with pytest.raises(ValueError):
        service.create_employee(
            admin,
            full_name="Employé",
            civility="Autre",
            email="employee@test.com",
            password="StrongPassword123!",
        )


def test_create_employee_rejects_duplicate_email(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    create_user(
        db_session,
        name="Employé existant",
        email="employee@test.com",
    )

    service = EmployeeService(db_session)

    with pytest.raises(ValueError):
        service.create_employee(
            admin,
            full_name="Nouvel employé",
            civility="Monsieur",
            email="EMPLOYEE@TEST.COM",
            password="StrongPassword123!",
        )


def test_admin_can_update_employee(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        name="Ancien nom",
        email="employee@test.com",
    )

    service = EmployeeService(db_session)

    updated = service.update_employee(
        admin,
        employee.id,
        full_name="Nouveau nom",
        civility="Monsieur",
        email="new@test.com",
    )

    assert updated.full_name == "Nouveau nom"
    assert updated.civility == "Monsieur"
    assert updated.email == "new@test.com"


def test_admin_cannot_update_another_admin(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    another_admin = create_user(
        db_session,
        name="Autre admin",
        email="other-admin@test.com",
        role=UserRole.ADMIN,
    )

    service = EmployeeService(db_session)

    with pytest.raises(ValueError):
        service.update_employee(
            admin,
            another_admin.id,
            civility="Monsieur",
        )


def test_update_rejects_duplicate_email(db_session):
    admin = create_user(
        db_session,
        name="Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
    )
    employee = create_user(
        db_session,
        name="Employé",
        email="employee@test.com",
    )
    create_user(
        db_session,
        name="Autre employé",
        email="other@test.com",
    )

    service = EmployeeService(db_session)

    with pytest.raises(ValueError):
        service.update_employee(
            admin,
            employee.id,
            email="other@test.com",
        )
