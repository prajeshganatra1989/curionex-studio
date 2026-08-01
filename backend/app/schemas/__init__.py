"""Pydantic request and response schemas."""

from app.schemas.audit import AuditLogListResponse, AuditLogResponse
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    normalize_email,
)
from app.schemas.knowledge_pack import (
    KnowledgePackCreate,
    KnowledgePackListResponse,
    KnowledgePackReorderRequest,
    KnowledgePackResponse,
    KnowledgePackSectionResponse,
    KnowledgePackSectionUpdate,
    KnowledgePackUpdate,
)
from app.schemas.project import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
    TagCreate,
    TagResponse,
    TagUpdate,
)
from app.schemas.rbac import (
    MessageResponse,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)

__all__ = [
    "AuditLogListResponse",
    "AuditLogResponse",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "KnowledgePackCreate",
    "KnowledgePackListResponse",
    "KnowledgePackReorderRequest",
    "KnowledgePackResponse",
    "KnowledgePackSectionResponse",
    "KnowledgePackSectionUpdate",
    "KnowledgePackUpdate",
    "LoginRequest",
    "MessageResponse",
    "PermissionResponse",
    "ProjectCreate",
    "ProjectListResponse",
    "ProjectMemberResponse",
    "ProjectResponse",
    "ProjectUpdate",
    "RoleCreate",
    "RoleResponse",
    "TagCreate",
    "TagResponse",
    "TagUpdate",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "normalize_email",
]
