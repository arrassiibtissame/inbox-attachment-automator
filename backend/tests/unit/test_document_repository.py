
from sqlalchemy.exc import IntegrityError
import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models import Client, User, UserRole
from backend.database.models import document
from backend.database.models import document
from backend.database.models.document import DocumentStatus
from backend.database.repositories.document_repository import DocumentRepository


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


def create_client(db_session, user, company_name="Test Company"):
    """Creates a client assigned to a responsible user."""

    client = Client(
        company_name=company_name,
        responsible_user_id=user.id,
    )

    db_session.add(client)
    db_session.flush()

    return client


def test_create_document_without_client(db_session):
    repository = DocumentRepository(db_session)

    document = repository.create()

    assert document.id is not None
    assert document.client_id is None
    assert document.status == DocumentStatus.TO_REVIEW


def test_get_by_id(db_session):
    repository = DocumentRepository(db_session)

    document = repository.create(
        document_type="FACTURE",
        document_number="FAC-001",
    )

    result = repository.get_by_id(document.id)

    assert result is not None
    assert result.document_type == "FACTURE"
    assert result.document_number == "FAC-001"


def test_list_all_returns_documents(db_session):
    repository = DocumentRepository(db_session)

    repository.create(document_type="FACTURE")
    repository.create(document_type="RELEVE_BANCAIRE")

    results = repository.list_all()

    assert len(results) == 2


def test_list_all_filters_by_status(db_session):
    repository = DocumentRepository(db_session)
    user = create_responsible_user(db_session)
    client = create_client(db_session, user)

    repository.create()
    repository.create(
        client_id=client.id,
        status=DocumentStatus.CLASSIFIED,
    )

    results = repository.list_all(
        status=DocumentStatus.TO_REVIEW
    )

    assert len(results) == 1
    assert results[0].status == DocumentStatus.TO_REVIEW


def test_list_by_client(db_session):
    repository = DocumentRepository(db_session)
    user = create_responsible_user(db_session)

    client_a = create_client(
        db_session,
        user,
        "Company A",
    )
    client_b = create_client(
        db_session,
        user,
        "Company B",
    )

    document_a = repository.create(client_id=client_a.id)
    repository.create(client_id=client_b.id)

    results = repository.list_by_client(client_a.id)

    assert len(results) == 1
    assert results[0].id == document_a.id


def test_list_by_client_filters_by_status(db_session):
    repository = DocumentRepository(db_session)
    user = create_responsible_user(db_session)
    client = create_client(db_session, user)

    repository.create(client_id=client.id)
    classified_document = repository.create(
        client_id=client.id,
        status=DocumentStatus.CLASSIFIED,
    )

    results = repository.list_by_client(
        client.id,
        status=DocumentStatus.CLASSIFIED,
    )

    assert len(results) == 1
    assert results[0].id == classified_document.id


def test_list_by_responsible_user_isolates_documents(db_session):
    repository = DocumentRepository(db_session)

    employee_a = create_responsible_user(
        db_session,
        "employee_a@test.com",
    )
    employee_b = create_responsible_user(
        db_session,
        "employee_b@test.com",
    )

    client_a = create_client(
        db_session,
        employee_a,
        "Company A",
    )
    client_b = create_client(
        db_session,
        employee_b,
        "Company B",
    )

    document_a = repository.create(client_id=client_a.id)
    repository.create(client_id=client_b.id)

    results = repository.list_by_responsible_user(
        employee_a.id
    )

    assert len(results) == 1
    assert results[0].id == document_a.id


def test_list_unassigned_returns_only_documents_to_review(
    db_session,
):
    repository = DocumentRepository(db_session)
    user = create_responsible_user(db_session)
    client = create_client(db_session, user)

    unassigned_document = repository.create()

    repository.create(client_id=client.id)

    repository.create(
        client_id=client.id,
        status=DocumentStatus.CLASSIFIED,
    )

    results = repository.list_unassigned()

    assert len(results) == 1
    assert results[0].id == unassigned_document.id
    assert results[0].client_id is None
    assert results[0].status == DocumentStatus.TO_REVIEW


def test_classified_document_requires_client(db_session):
    repository = DocumentRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            status=DocumentStatus.CLASSIFIED,
        )

    db_session.rollback()

    assert repository.list_all() == []

def test_list_by_client_filters_by_category(db_session):
    repository = DocumentRepository(db_session)
    user = create_responsible_user(db_session)
    client = create_client(db_session, user)

    legal_document = repository.create(
        client_id=client.id,
        document_type="STATUTS",
        category="Juridique",
    )
    repository.create(
        client_id=client.id,
        document_type="FACTURE",
        category="Fiscalit" + chr(233),
    )
    repository.create(
        client_id=client.id,
        document_type="AUTRE",
    )

    results = repository.list_by_client(
        client.id,
        category="Juridique",
    )

    assert len(results) == 1
    assert results[0].id == legal_document.id
    assert results[0].category == "Juridique"


def test_create_document_without_category(db_session):
    repository = DocumentRepository(db_session)

    document = repository.create()

    assert document.category is None


def test_create_document_rejects_unknown_category(db_session):
    repository = DocumentRepository(db_session)

    with pytest.raises(ValueError, match="Cat"):
        repository.create(category="Autre")


def test_list_by_client_rejects_unknown_category(db_session):
    repository = DocumentRepository(db_session)

    with pytest.raises(ValueError, match="Cat"):
        repository.list_by_client(1, category="Autre")
