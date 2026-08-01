"""Shared pytest fixtures for database-backed tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401 — register models on metadata
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_settings():
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.DATABASE_URL.startswith("postgresql"):
        pytest.skip("PostgreSQL DATABASE_URL is required for database tests")
    if not settings.JWT_SECRET_KEY.strip():
        pytest.skip("JWT_SECRET_KEY is required for authentication tests")
    return settings


@pytest.fixture(scope="session")
def engine(test_settings):
    engine = create_engine(test_settings.DATABASE_URL, poolclass=NullPool)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    # Ensure schema exists without dropping developer data at teardown.
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = SessionLocal()
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session: Session, trans) -> None:  # noqa: ANN001
        nonlocal nested
        if connection.closed:
            return
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
