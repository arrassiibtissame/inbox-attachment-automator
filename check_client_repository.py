from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.database.connection import Base
from backend.database import models
from backend.database.models.user import User
from backend.database.repositories.client_repository import ClientRepository


# Create an isolated in-memory SQLite database.
test_engine = create_engine("sqlite+pysqlite:///:memory:")


# Enable foreign keys for this test database.
@event.listens_for(test_engine, "connect")
def enable_foreign_keys(connection, record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create tables only in the temporary database.
Base.metadata.create_all(test_engine)


try:
    with Session(test_engine) as session:

        # 1. Create a test user.
        user = User(
            full_name="Test Employee",
            email="test.employee@example.com",
            password_hash="test-only-hash",
        )

        session.add(user)
        session.flush()

        repository = ClientRepository(session)

        # 2. Create two clients with the same IF.
        client1 = repository.create(
            company_name="Test Company Alpha",
            responsible_user_id=user.id,
            internal_code="TEST-001",
            ice="001234567000001",
            if_number="12345678",
        )

        client2 = repository.create(
            company_name="Test Company Beta",
            responsible_user_id=user.id,
            internal_code="TEST-002",
            ice="001234567000002",
            if_number="12345678",
        )

        # Make the second client inactive.
        client2.is_active = False
        session.flush()

        # 3. Test retrieval by ID.
        assert repository.get_by_id(client1.id).company_name == "Test Company Alpha"
        print("PASS: get_by_id")

        # 4. Test retrieval by ICE.
        assert repository.get_by_ice("001234567000001").id == client1.id
        print("PASS: get_by_ice")

        # 5. Test retrieval by internal code.
        assert repository.get_by_internal_code("TEST-002").id == client2.id
        print("PASS: get_by_internal_code")

        # 6. Test IF search (two results expected).
        clients_by_if = repository.list_by_if_number("12345678")
        assert len(clients_by_if) == 2
        print("PASS: list_by_if_number")

        # 7. Test responsible user and active filter.
        active_clients = repository.list_by_responsible_user(user.id)
        assert len(active_clients) == 1
        assert active_clients[0].id == client1.id

        all_clients = repository.list_by_responsible_user(
            user.id,
            active_only=False,
        )
        assert len(all_clients) == 2
        print("PASS: list_by_responsible_user")

        # 8. Roll back everything.
        session.rollback()
        print("PASS: rollback")

finally:
    test_engine.dispose()


print("\nAll ClientRepository tests passed!")
