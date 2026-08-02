"""Editorial Library constants."""

TOPIC_STATUS_IDEA = "idea"
TOPIC_STATUS_PLANNED = "planned"
TOPIC_STATUS_IN_PROGRESS = "in_progress"
TOPIC_STATUS_PROJECT_CREATED = "project_created"
TOPIC_STATUS_PUBLISHED = "published"
TOPIC_STATUS_ARCHIVED = "archived"

TOPIC_STATUSES: frozenset[str] = frozenset(
    {
        TOPIC_STATUS_IDEA,
        TOPIC_STATUS_PLANNED,
        TOPIC_STATUS_IN_PROGRESS,
        TOPIC_STATUS_PROJECT_CREATED,
        TOPIC_STATUS_PUBLISHED,
        TOPIC_STATUS_ARCHIVED,
    }
)

DEFAULT_TOPIC_STATUS = TOPIC_STATUS_IDEA

TOPIC_DIFFICULTY_EASY = "easy"
TOPIC_DIFFICULTY_MEDIUM = "medium"
TOPIC_DIFFICULTY_HARD = "hard"

TOPIC_DIFFICULTIES: frozenset[str] = frozenset(
    {
        TOPIC_DIFFICULTY_EASY,
        TOPIC_DIFFICULTY_MEDIUM,
        TOPIC_DIFFICULTY_HARD,
    }
)

DEFAULT_TOPIC_DIFFICULTY = TOPIC_DIFFICULTY_MEDIUM

TOPIC_VIRAL_LOW = "low"
TOPIC_VIRAL_MEDIUM = "medium"
TOPIC_VIRAL_HIGH = "high"

TOPIC_VIRAL_POTENTIALS: frozenset[str] = frozenset(
    {
        TOPIC_VIRAL_LOW,
        TOPIC_VIRAL_MEDIUM,
        TOPIC_VIRAL_HIGH,
    }
)

DEFAULT_TOPIC_VIRAL = TOPIC_VIRAL_MEDIUM

# Soft-archive statuses excluded from default browse unless filtered.
ACTIVE_TOPIC_STATUSES: frozenset[str] = frozenset(
    TOPIC_STATUSES - {TOPIC_STATUS_ARCHIVED}
)

# Categories used by the evergreen seed catalog.
EDITORIAL_CATEGORIES: tuple[str, ...] = (
    "Human Brain",
    "Psychology",
    "Space",
    "Earth",
    "Science",
    "Technology",
    "History",
    "Animals",
    "Human Body",
    "Biology",
)

# Statuses that may transition to project_created via Create Project.
CREATE_PROJECT_ALLOWED_STATUSES: frozenset[str] = frozenset(
    {
        TOPIC_STATUS_IDEA,
        TOPIC_STATUS_PLANNED,
        TOPIC_STATUS_IN_PROGRESS,
    }
)

TOPIC_PRIORITY_A = "A"
TOPIC_PRIORITY_B = "B"
TOPIC_PRIORITY_C = "C"

TOPIC_PRIORITIES: frozenset[str] = frozenset(
    {
        TOPIC_PRIORITY_A,
        TOPIC_PRIORITY_B,
        TOPIC_PRIORITY_C,
    }
)

DEFAULT_TOPIC_PRIORITY = TOPIC_PRIORITY_B

PRODUCTION_WAVES: frozenset[int] = frozenset({1, 2, 3, 4})
DEFAULT_PRODUCTION_WAVE = 4
