"""Controlled ContentVersion and Approval status values."""

# ContentVersion lifecycle
VERSION_STATUS_DRAFT = "draft"
VERSION_STATUS_IN_REVIEW = "in_review"
VERSION_STATUS_APPROVED = "approved"
VERSION_STATUS_REJECTED = "rejected"
VERSION_STATUS_ARCHIVED = "archived"

VERSION_STATUSES: frozenset[str] = frozenset(
    {
        VERSION_STATUS_DRAFT,
        VERSION_STATUS_IN_REVIEW,
        VERSION_STATUS_APPROVED,
        VERSION_STATUS_REJECTED,
        VERSION_STATUS_ARCHIVED,
    }
)

DEFAULT_VERSION_STATUS = VERSION_STATUS_DRAFT

# Approval lifecycle
APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_REJECTED = "rejected"
APPROVAL_STATUS_CANCELLED = "cancelled"

APPROVAL_STATUSES: frozenset[str] = frozenset(
    {
        APPROVAL_STATUS_PENDING,
        APPROVAL_STATUS_APPROVED,
        APPROVAL_STATUS_REJECTED,
        APPROVAL_STATUS_CANCELLED,
    }
)
