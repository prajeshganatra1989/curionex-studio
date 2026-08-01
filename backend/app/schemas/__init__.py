"""Pydantic request and response schemas."""

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    normalize_email,
)
from app.schemas.rbac import (
    MessageResponse,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)

__all__ = [
    "LoginRequest",
    "MessageResponse",
    "PermissionResponse",
    "RoleCreate",
    "RoleResponse",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "normalize_email",
]
