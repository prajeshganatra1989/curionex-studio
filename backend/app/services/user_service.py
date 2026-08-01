"""User domain services."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_USER_CREATED,
    ACTION_USER_DEACTIVATED,
    ACTION_USER_UPDATED,
    ENTITY_USER,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate, normalize_email
from app.services.audit_service import record_audit_event


class DuplicateEmailError(Exception):
    """Raised when creating a user with an email that already exists."""


class AuthenticationError(Exception):
    """Raised for any failed authentication attempt (generic)."""


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by normalized email."""
    normalized = normalize_email(email)
    statement = select(User).where(User.email == normalized)
    return db.scalar(statement)


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetch a user by primary key."""
    return db.get(User, user_id)


def create_user(
    db: Session,
    payload: UserCreate,
    *,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Create a user with a hashed password.

    This is an internal service for admin/CLI/bootstrap use — not public signup.
    """
    user = User(
        email=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True,
    )
    db.add(user)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_USER_CREATED,
            entity_type=ENTITY_USER,
            entity_id=user.id,
            metadata={"email": user.email},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError("A user with this email already exists.") from exc
    db.refresh(user)
    return user


def update_user_profile(
    db: Session,
    user_id: UUID,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Update basic profile fields and record an audit event."""
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError("User not found.")

    changed: list[str] = []
    if first_name is not None and first_name != user.first_name:
        user.first_name = first_name
        changed.append("first_name")
    if last_name is not None and last_name != user.last_name:
        user.last_name = last_name
        changed.append("last_name")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_USER_UPDATED,
            entity_type=ENTITY_USER,
            entity_id=user.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        db.refresh(user)
    return user


def deactivate_user(
    db: Session,
    user_id: UUID,
    *,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Deactivate a user account and record an audit event."""
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError("User not found.")
    if not user.is_active:
        return user

    user.is_active = False
    record_audit_event(
        db,
        actor_user_id=actor_user_id,
        action=ACTION_USER_DEACTIVATED,
        entity_type=ENTITY_USER,
        entity_id=user.id,
        metadata={"email": user.email},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate by email/password.

    Always raises AuthenticationError on failure so callers cannot distinguish
    missing users, bad passwords, or inactive accounts.
    """
    user = get_user_by_email(db, email)
    if user is None:
        raise AuthenticationError("Invalid email or password.")
    if not user.is_active:
        raise AuthenticationError("Invalid email or password.")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    return user


def issue_access_token_for_user(user: User) -> str:
    """Create a JWT access token for an authenticated user."""
    return create_access_token(subject=user.id)
