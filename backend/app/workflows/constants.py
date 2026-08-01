"""Controlled ContentWorkflow stages and statuses."""

WORKFLOW_STAGE_WORKSPACE = "workspace"
WORKFLOW_STAGE_VERSIONING = "versioning"
WORKFLOW_STAGE_REVIEW = "review"
WORKFLOW_STAGE_COMPLETED = "completed"

WORKFLOW_STAGES: frozenset[str] = frozenset(
    {
        WORKFLOW_STAGE_WORKSPACE,
        WORKFLOW_STAGE_VERSIONING,
        WORKFLOW_STAGE_REVIEW,
        WORKFLOW_STAGE_COMPLETED,
    }
)

DEFAULT_WORKFLOW_STAGE = WORKFLOW_STAGE_WORKSPACE

WORKFLOW_STATUS_ACTIVE = "active"
WORKFLOW_STATUS_BLOCKED = "blocked"
WORKFLOW_STATUS_COMPLETED = "completed"
WORKFLOW_STATUS_ARCHIVED = "archived"

WORKFLOW_STATUSES: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_ACTIVE,
        WORKFLOW_STATUS_BLOCKED,
        WORKFLOW_STATUS_COMPLETED,
        WORKFLOW_STATUS_ARCHIVED,
    }
)

DEFAULT_WORKFLOW_STATUS = WORKFLOW_STATUS_ACTIVE

# Explicit stage transition map (archive is a status change, not a stage).
WORKFLOW_STAGE_TRANSITIONS: dict[str, frozenset[str]] = {
    WORKFLOW_STAGE_WORKSPACE: frozenset({WORKFLOW_STAGE_VERSIONING}),
    WORKFLOW_STAGE_VERSIONING: frozenset({WORKFLOW_STAGE_REVIEW}),
    WORKFLOW_STAGE_REVIEW: frozenset(
        {WORKFLOW_STAGE_WORKSPACE, WORKFLOW_STAGE_COMPLETED}
    ),
    WORKFLOW_STAGE_COMPLETED: frozenset(),
}

# Stages that may be archived via the archive endpoint (not a stage change).
ARCHIVEABLE_STAGES: frozenset[str] = frozenset(
    {
        WORKFLOW_STAGE_WORKSPACE,
        WORKFLOW_STAGE_VERSIONING,
        WORKFLOW_STAGE_REVIEW,
    }
)
