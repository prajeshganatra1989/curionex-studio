"""Database foundation tests (no live PostgreSQL required)."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import Settings
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.main import app

client = TestClient(app)


def test_settings_include_database_url() -> None:
    settings = Settings(
        DATABASE_URL=(
            "postgresql+psycopg://username:password@localhost:5432/curionex_studio"
        )
    )
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")
    assert "curionex_studio" in settings.DATABASE_URL


def test_sqlalchemy_base_is_declarative() -> None:
    assert issubclass(Base, DeclarativeBase)
    assert Base.metadata is not None


def test_engine_and_session_factory_are_configured() -> None:
    assert engine is not None
    assert engine.url.get_backend_name() == "postgresql"
    assert SessionLocal is not None


def test_get_db_yields_and_closes_session() -> None:
    mock_session = MagicMock(spec=Session)
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        generator: Generator[Session, None, None] = get_db()
        session = next(generator)
        assert session is mock_session
        generator.close()
        mock_session.close.assert_called_once()


def test_health_db_returns_ok_when_database_is_reachable() -> None:
    with patch("app.api.routes.health.check_database_connection") as probe:
        probe.return_value = None
        response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    probe.assert_called_once()


def test_health_db_returns_503_when_database_is_unavailable() -> None:
    with patch(
        "app.api.routes.health.check_database_connection",
        side_effect=ConnectionError("connection refused"),
    ):
        response = client.get("/health/db")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["status"] == "error"
    assert detail["database"] == "unavailable"
    assert "password" not in str(response.json()).lower()
    assert "postgresql+psycopg" not in str(response.json()).lower()
