"""SQLAlchemy declarative base for ORM models.

All application models must subclass ``Base`` so Alembic can discover
their metadata when generating migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for Curionex Studio models."""
