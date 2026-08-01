"""Controlled project status values (application-enforced)."""

PROJECT_STATUS_DRAFT = "draft"
PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_ARCHIVED = "archived"

PROJECT_STATUSES: frozenset[str] = frozenset(
    {
        PROJECT_STATUS_DRAFT,
        PROJECT_STATUS_ACTIVE,
        PROJECT_STATUS_ARCHIVED,
    }
)

DEFAULT_PROJECT_STATUS = PROJECT_STATUS_DRAFT

# PostgreSQL sequence used for concurrency-safe project_code allocation.
PROJECT_CODE_SEQUENCE = "project_code_seq"
