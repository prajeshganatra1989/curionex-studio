"""AI foundation constants — providers, job states, prompt statuses."""

from __future__ import annotations

# Provider codes (registry keys)
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GEMINI = "gemini"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_AZURE_OPENAI = "azure_openai"
PROVIDER_OLLAMA = "ollama"

PROVIDER_CODES: frozenset[str] = frozenset(
    {
        PROVIDER_OPENAI,
        PROVIDER_ANTHROPIC,
        PROVIDER_GEMINI,
        PROVIDER_OPENROUTER,
        PROVIDER_AZURE_OPENAI,
        PROVIDER_OLLAMA,
    }
)

# Prompt lifecycle
PROMPT_STATUS_DRAFT = "draft"
PROMPT_STATUS_ACTIVE = "active"
PROMPT_STATUS_ARCHIVED = "archived"

PROMPT_STATUSES: frozenset[str] = frozenset(
    {
        PROMPT_STATUS_DRAFT,
        PROMPT_STATUS_ACTIVE,
        PROMPT_STATUS_ARCHIVED,
    }
)

PROMPT_VERSION_STATUS_DRAFT = "draft"
PROMPT_VERSION_STATUS_ACTIVE = "active"
PROMPT_VERSION_STATUS_SUPERSEDED = "superseded"

PROMPT_VERSION_STATUSES: frozenset[str] = frozenset(
    {
        PROMPT_VERSION_STATUS_DRAFT,
        PROMPT_VERSION_STATUS_ACTIVE,
        PROMPT_VERSION_STATUS_SUPERSEDED,
    }
)

# Job lifecycle
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

JOB_STATUSES: frozenset[str] = frozenset(
    {
        JOB_STATUS_QUEUED,
        JOB_STATUS_RUNNING,
        JOB_STATUS_COMPLETED,
        JOB_STATUS_FAILED,
        JOB_STATUS_CANCELLED,
    }
)

# Known template variables (extensible — unknown vars still allowed if declared)
KNOWN_PROMPT_VARIABLES: frozenset[str] = frozenset(
    {
        "topic",
        "research",
        "audience",
        "facts",
        "sources",
        "tone",
        "length",
        "language",
        "content_angle",
        "key_insights",
        "script_title",
        "project_name",
    }
)

MAX_JOB_RETRIES = 3
