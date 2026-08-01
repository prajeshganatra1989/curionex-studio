"""Stable audit action codes and entity type labels."""

# Entity types (logical — not polymorphic FKs)
ENTITY_USER = "user"
ENTITY_ROLE = "role"
ENTITY_PERMISSION = "permission"
ENTITY_AUTHENTICATION = "authentication"
ENTITY_PROJECT = "project"
ENTITY_CATEGORY = "category"
ENTITY_TAG = "tag"
ENTITY_KNOWLEDGE_PACK = "knowledge_pack"

# Action codes
ACTION_USER_CREATED = "user.created"
ACTION_USER_UPDATED = "user.updated"
ACTION_USER_DEACTIVATED = "user.deactivated"

ACTION_ROLE_CREATED = "role.created"
ACTION_ROLE_UPDATED = "role.updated"
ACTION_ROLE_ASSIGNED = "role.assigned"
ACTION_ROLE_REMOVED = "role.removed"

ACTION_PERMISSION_ASSIGNED = "permission.assigned"

ACTION_AUTH_LOGIN = "authentication.login"
ACTION_AUTH_LOGIN_FAILED = "authentication.login_failed"

ACTION_PROJECT_CREATED = "project.created"
ACTION_PROJECT_UPDATED = "project.updated"
ACTION_PROJECT_ARCHIVED = "project.archived"
ACTION_PROJECT_MEMBER_ADDED = "project.member_added"
ACTION_PROJECT_MEMBER_REMOVED = "project.member_removed"

ACTION_CATEGORY_CREATED = "category.created"
ACTION_CATEGORY_UPDATED = "category.updated"

ACTION_TAG_CREATED = "tag.created"
ACTION_TAG_UPDATED = "tag.updated"

ACTION_KNOWLEDGE_PACK_CREATED = "knowledge_pack.created"
ACTION_KNOWLEDGE_PACK_UPDATED = "knowledge_pack.updated"
ACTION_KNOWLEDGE_PACK_ARCHIVED = "knowledge_pack.archived"
ACTION_KNOWLEDGE_PACK_SECTION_UPDATED = "knowledge_pack.section_updated"
ACTION_KNOWLEDGE_PACK_SECTIONS_REORDERED = "knowledge_pack.sections_reordered"
