"""Database engine, session factory, and connectivity helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine: Engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session for FastAPI Depends(...)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> None:
    """Run a lightweight connectivity probe against PostgreSQL.

    Raises the underlying SQLAlchemy/DBAPI error when the database is unreachable.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
