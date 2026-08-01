"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.audit.actions import (
    ACTION_AUTH_LOGIN,
    ACTION_AUTH_LOGIN_FAILED,
    ENTITY_AUTHENTICATION,
    ENTITY_USER,
)
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.audit_service import record_audit_event
from app.services.user_service import (
    AuthenticationError,
    authenticate_user,
    issue_access_token_for_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with email/password and return a JWT access token."""
    ctx = extract_request_audit_context(request)
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthenticationError:
        record_audit_event(
            db,
            actor_user_id=None,
            action=ACTION_AUTH_LOGIN_FAILED,
            entity_type=ENTITY_AUTHENTICATION,
            entity_id=None,
            metadata={"reason": "invalid_credentials"},
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        ) from None

    record_audit_event(
        db,
        actor_user_id=user.id,
        action=ACTION_AUTH_LOGIN,
        entity_type=ENTITY_USER,
        entity_id=user.id,
        metadata=None,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    db.commit()
    token = issue_access_token_for_user(user)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the authenticated user profile."""
    return current_user
