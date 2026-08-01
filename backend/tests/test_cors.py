"""CORS configuration tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.cors import configure_cors
from app.main import create_app


def test_cors_allows_configured_origin(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )
    get_settings.cache_clear()


def test_cors_rejects_unknown_origin(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None
    get_settings.cache_clear()


def test_wildcard_disables_credentials() -> None:
    settings = Settings(CORS_ORIGINS="*")
    assert settings.cors_origin_list == ["*"]
    application = FastAPI()
    configure_cors(application, settings)
    assert len(application.user_middleware) == 1
    middleware = application.user_middleware[0]
    kwargs = middleware.kwargs
    assert kwargs.get("allow_origins") == ["*"]
    assert kwargs.get("allow_credentials") is False


def test_empty_cors_skips_middleware() -> None:
    settings = Settings(CORS_ORIGINS="")
    application = FastAPI()
    configure_cors(application, settings)
    assert application.user_middleware == []
