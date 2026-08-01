"""Authentication and user service tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import UserCreate
from app.services.user_service import (
    AuthenticationError,
    DuplicateEmailError,
    authenticate_user,
    create_user,
    get_user_by_email,
)


def _create_payload(
    email: str = "user@example.com",
    password: str = "securepass123",
) -> UserCreate:
    return UserCreate(
        email=email,
        password=password,
        first_name="Ada",
        last_name="Lovelace",
    )


def test_password_is_hashed_and_verified() -> None:
    password = "securepass123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert not password_hash.startswith(password)
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_create_user_hashes_password(db_session: Session) -> None:
    user = create_user(db_session, _create_payload())

    assert user.id is not None
    assert user.email == "user@example.com"
    assert user.password_hash != "securepass123"
    assert verify_password("securepass123", user.password_hash)


def test_duplicate_email_is_rejected(db_session: Session) -> None:
    create_user(db_session, _create_payload("dup@example.com"))
    with pytest.raises(DuplicateEmailError):
        create_user(db_session, _create_payload("Dup@Example.com"))


def test_email_is_normalized(db_session: Session) -> None:
    user = create_user(db_session, _create_payload("  Mixed.Case@Example.COM "))
    assert user.email == "mixed.case@example.com"
    assert get_user_by_email(db_session, "mixed.case@example.com") is not None


def test_login_succeeds(client: TestClient, db_session: Session) -> None:
    create_user(db_session, _create_payload("login@example.com"))

    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "password" not in body
    assert "password_hash" not in body


def test_login_fails_with_invalid_credentials(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(db_session, _create_payload("valid@example.com"))

    missing = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "securepass123"},
    )
    wrong = client.post(
        "/auth/login",
        json={"email": "valid@example.com", "password": "wrong-password"},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]
    assert "not found" not in missing.json()["detail"].lower()
    assert "password" not in missing.json()["detail"].lower() or (
        missing.json()["detail"] == "Invalid email or password."
    )


def test_inactive_user_cannot_login(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session, _create_payload("inactive@example.com"))
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "securepass123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_authenticate_user_service_rejects_bad_password(db_session: Session) -> None:
    create_user(db_session, _create_payload("svc@example.com"))
    with pytest.raises(AuthenticationError):
        authenticate_user(db_session, "svc@example.com", "nope")


def test_valid_jwt_is_accepted() -> None:
    user_id = uuid4()
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)


def test_invalid_jwt_is_rejected() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-valid-token")


def test_expired_jwt_is_rejected() -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        settings.require_jwt_secret(),
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_auth_me_works_with_valid_token(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, _create_payload("me@example.com"))
    login = client.post(
        "/auth/login",
        json={"email": "me@example.com", "password": "securepass123"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "me@example.com"
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_auth_me_fails_without_token(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_fails_with_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer totally-invalid"},
    )
    assert response.status_code == 401


def test_auth_me_fails_for_inactive_user(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, _create_payload("gone@example.com"))
    token = create_access_token(subject=user.id)
    user.is_active = False
    db_session.commit()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_user_response_never_exposes_password_hash(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(db_session, _create_payload("safe@example.com"))
    login = client.post(
        "/auth/login",
        json={"email": "safe@example.com", "password": "securepass123"},
    )
    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    serialized = me.text.lower()
    assert "password_hash" not in serialized
    assert "argon2" not in serialized
    db_user = get_user_by_email(db_session, "safe@example.com")
    assert db_user is not None
    assert db_user.password_hash.startswith("$argon2")
