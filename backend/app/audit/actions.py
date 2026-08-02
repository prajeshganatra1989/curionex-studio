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

ENTITY_CONTENT_VERSION = "content_version"
ENTITY_APPROVAL = "approval"

ACTION_CONTENT_VERSION_CREATED = "content_version.created"
ACTION_APPROVAL_REQUESTED = "approval.requested"
ACTION_APPROVAL_APPROVED = "approval.approved"
ACTION_APPROVAL_REJECTED = "approval.rejected"
ACTION_APPROVAL_CANCELLED = "approval.cancelled"

ENTITY_SCRIPT = "script"

ACTION_SCRIPT_CREATED = "script.created"
ACTION_SCRIPT_UPDATED = "script.updated"
ACTION_SCRIPT_ARCHIVED = "script.archived"
ACTION_SCRIPT_DOCUMENT_UPDATED = "script.document_updated"

ACTION_SCRIPT_AI_DRAFT_REQUESTED = "script.ai_draft_requested"
ACTION_SCRIPT_AI_DRAFT_COMPLETED = "script.ai_draft_completed"
ACTION_SCRIPT_AI_DRAFT_FAILED = "script.ai_draft_failed"
ACTION_SCRIPT_AI_DRAFT_APPLIED = "script.ai_draft_applied"

ACTION_SCRIPT_QUALITY_REVIEW_REQUESTED = "script.quality_review_requested"
ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED = "script.quality_review_completed"
ACTION_SCRIPT_QUALITY_REVIEW_FAILED = "script.quality_review_failed"
ACTION_SCRIPT_QUALITY_SUGGESTION_APPLIED = "script.quality_suggestion_applied"

ENTITY_WORKFLOW = "workflow"

ACTION_WORKFLOW_CREATED = "workflow.created"
ACTION_WORKFLOW_STAGE_CHANGED = "workflow.stage_changed"
ACTION_WORKFLOW_VERSION_CREATED = "workflow.version_created"
ACTION_WORKFLOW_REVIEW_SUBMITTED = "workflow.review_submitted"
ACTION_WORKFLOW_COMPLETED = "workflow.completed"
ACTION_WORKFLOW_RETURNED_TO_WORKSPACE = "workflow.returned_to_workspace"
ACTION_WORKFLOW_ARCHIVED = "workflow.archived"

ENTITY_AI_PROVIDER = "ai_provider"
ENTITY_AI_MODEL = "ai_model"
ENTITY_AI_PROMPT = "ai_prompt"
ENTITY_AI_PROMPT_VERSION = "ai_prompt_version"
ENTITY_AI_JOB = "ai_job"
ENTITY_AI_SETTINGS = "ai_settings"

ACTION_AI_PROMPT_CREATED = "ai.prompt_created"
ACTION_AI_PROMPT_UPDATED = "ai.prompt_updated"
ACTION_AI_PROMPT_VERSION_CREATED = "ai.prompt_version_created"
ACTION_AI_PROMPT_VERSION_ACTIVATED = "ai.prompt_version_activated"
ACTION_AI_JOB_QUEUED = "ai.job_queued"
ACTION_AI_JOB_STARTED = "ai.job_started"
ACTION_AI_JOB_COMPLETED = "ai.job_completed"
ACTION_AI_JOB_FAILED = "ai.job_failed"
ACTION_AI_JOB_CANCELLED = "ai.job_cancelled"
ACTION_AI_SETTINGS_CHANGED = "ai.settings_changed"
ACTION_AI_PROVIDER_UPDATED = "ai.provider_updated"
ACTION_AI_PROVIDER_CREDENTIALS_SET = "ai.provider_credentials_set"
ACTION_AI_PROVIDER_CREDENTIALS_CLEARED = "ai.provider_credentials_cleared"
ACTION_AI_MODEL_UPDATED = "ai.model_updated"
ACTION_KNOWLEDGE_PACK_AI_DRAFT_APPLIED = "knowledge_pack.ai_draft_applied"

ENTITY_PRODUCTION_SETTINGS = "production_settings"
ACTION_PRODUCTION_SETTINGS_UPDATED = "production.settings_updated"

ENTITY_EDITORIAL_TOPIC = "editorial_topic"
ACTION_EDITORIAL_TOPIC_CREATED = "editorial_topic.created"
ACTION_EDITORIAL_TOPIC_UPDATED = "editorial_topic.updated"
ACTION_EDITORIAL_TOPIC_ARCHIVED = "editorial_topic.archived"
ACTION_EDITORIAL_TOPIC_PROJECT_LINKED = "editorial_topic.project_linked"
