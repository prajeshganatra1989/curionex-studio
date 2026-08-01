"""Stable audit action codes and entity type labels."""

# Entity types (logical — not polymorphic FKs)
ENTITY_USER = "user"
ENTITY_ROLE = "role"
ENTITY_PERMISSION = "permission"
ENTITY_AUTHENTICATION = "authentication"

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
