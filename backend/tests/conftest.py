
import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.database.connection import Base
import backend.database.models  # Enregistre tous les modèles dans Base.metadata


@pytest.fixture
def test_engine():
    """Crée une base SQLite isolée pour chaque test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Fournit une session SQLAlchemy propre à chaque test."""

    with Session(test_engine) as session:
        yield session
        session.rollback()
