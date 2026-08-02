"""Initial RBAC permission and role catalogs (configurable seed data)."""

from __future__ import annotations

# Stable permission codes used by authorization checks.
PERMISSION_CATALOG: list[dict[str, str]] = [
    {"code": "users.view", "name": "View users", "description": "List and view users"},
    {
        "code": "users.create",
        "name": "Create users",
        "description": "Create user accounts",
    },
    {
        "code": "users.update",
        "name": "Update users",
        "description": "Update user profiles",
    },
    {
        "code": "users.deactivate",
        "name": "Deactivate users",
        "description": "Deactivate user accounts",
    },
    {
        "code": "roles.view",
        "name": "View roles",
        "description": "List roles and permissions",
    },
    {"code": "roles.create", "name": "Create roles", "description": "Create roles"},
    {
        "code": "roles.update",
        "name": "Update roles",
        "description": "Update roles and grants",
    },
    {
        "code": "roles.assign",
        "name": "Assign roles",
        "description": "Assign roles to users",
    },
    {"code": "projects.view", "name": "View projects", "description": "View projects"},
    {
        "code": "projects.create",
        "name": "Create projects",
        "description": "Create projects",
    },
    {
        "code": "projects.update",
        "name": "Update projects",
        "description": "Update projects",
    },
    {
        "code": "projects.delete",
        "name": "Delete projects",
        "description": "Delete projects",
    },
    {
        "code": "knowledge_packs.view",
        "name": "View knowledge packs",
        "description": "View knowledge packs",
    },
    {
        "code": "knowledge_packs.create",
        "name": "Create knowledge packs",
        "description": "Create knowledge packs",
    },
    {
        "code": "knowledge_packs.update",
        "name": "Update knowledge packs",
        "description": "Update knowledge packs",
    },
    {
        "code": "knowledge_packs.delete",
        "name": "Delete knowledge packs",
        "description": "Delete knowledge packs",
    },
    {"code": "scripts.view", "name": "View scripts", "description": "View scripts"},
    {
        "code": "scripts.create",
        "name": "Create scripts",
        "description": "Create scripts",
    },
    {
        "code": "scripts.update",
        "name": "Update scripts",
        "description": "Update scripts",
    },
    {
        "code": "scripts.delete",
        "name": "Delete scripts",
        "description": "Delete scripts",
    },
    {
        "code": "workflows.view",
        "name": "View workflows",
        "description": "View content production workflows",
    },
    {
        "code": "workflows.update",
        "name": "Update workflows",
        "description": "Transition and update content production workflows",
    },
    {
        "code": "versions.view",
        "name": "View versions",
        "description": "View content versions",
    },
    {
        "code": "versions.create",
        "name": "Create versions",
        "description": "Create content versions",
    },
    {
        "code": "content_versions.view",
        "name": "View content versions",
        "description": "View immutable content versions",
    },
    {
        "code": "content_versions.create",
        "name": "Create content versions",
        "description": "Create immutable content version snapshots",
    },
    {
        "code": "approvals.view",
        "name": "View approvals",
        "description": "View approvals",
    },
    {
        "code": "approvals.create",
        "name": "Create approvals",
        "description": "Submit for approval",
    },
    {"code": "approvals.approve", "name": "Approve", "description": "Approve content"},
    {
        "code": "approvals.reject",
        "name": "Reject",
        "description": "Reject / request changes",
    },
    {
        "code": "approvals.review",
        "name": "Review approvals",
        "description": "Approve or reject pending approvals",
    },
    {"code": "audit.view", "name": "View audit logs", "description": "View audit logs"},
    {
        "code": "settings.view",
        "name": "View settings",
        "description": "View system settings",
    },
    {
        "code": "settings.update",
        "name": "Update settings",
        "description": "Update system settings",
    },
    {
        "code": "ai.view",
        "name": "View AI foundation",
        "description": "View AI providers, models, jobs, and generations",
    },
    {
        "code": "ai.manage",
        "name": "Manage AI settings",
        "description": "Manage AI providers, credentials, models, and settings",
    },
    {
        "code": "ai.generate",
        "name": "Queue AI jobs",
        "description": "Queue AI generation jobs (no live generation in v0.16.0)",
    },
    {
        "code": "prompt.manage",
        "name": "Manage prompts",
        "description": "Create and version AI prompts",
    },
    {
        "code": "production.view",
        "name": "View Production Mode",
        "description": "View Production Mode overview, queue, and metrics",
    },
    {
        "code": "production.manage",
        "name": "Manage production goals",
        "description": "Manage Production Mode goals and settings",
    },
    {
        "code": "editorial_topics.view",
        "name": "View editorial topics",
        "description": "View Editorial Library topics",
    },
    {
        "code": "editorial_topics.create",
        "name": "Create editorial topics",
        "description": "Create Editorial Library topics",
    },
    {
        "code": "editorial_topics.update",
        "name": "Update editorial topics",
        "description": "Update Editorial Library topics and link projects",
    },
    {
        "code": "editorial_topics.delete",
        "name": "Archive editorial topics",
        "description": "Soft-archive Editorial Library topics",
    },
    {
        "code": "content_standards.view",
        "name": "View content standards",
        "description": "View the Curionex Content Standard",
    },
    {
        "code": "content_standards.manage",
        "name": "Manage content standards",
        "description": "Create, update, activate, and archive Content Standards",
    },
]

ALL_PERMISSION_CODES: list[str] = [item["code"] for item in PERMISSION_CATALOG]

# Role names are display labels only — authorization uses permission codes.
ROLE_CATALOG: dict[str, dict] = {
    "Owner": {
        "description": "Full platform access for the account owner.",
        "permissions": list(ALL_PERMISSION_CODES),
    },
    "Admin": {
        "description": "Administrative access excluding ownership-only future concerns.",
        "permissions": list(ALL_PERMISSION_CODES),
    },
    "Content Manager": {
        "description": "Manages projects, packs, and scripts.",
        "permissions": [
            "projects.view",
            "projects.create",
            "projects.update",
            "knowledge_packs.view",
            "knowledge_packs.create",
            "knowledge_packs.update",
            "scripts.view",
            "scripts.create",
            "scripts.update",
            "workflows.view",
            "workflows.update",
            "versions.view",
            "versions.create",
            "content_versions.view",
            "content_versions.create",
            "approvals.view",
            "approvals.create",
            "ai.view",
            "ai.manage",
            "ai.generate",
            "prompt.manage",
            "production.view",
            "production.manage",
            "editorial_topics.view",
            "editorial_topics.create",
            "editorial_topics.update",
            "editorial_topics.delete",
            "content_standards.view",
            "content_standards.manage",
        ],
    },
    "Script Writer": {
        "description": "Creates and edits scripts within accessible projects.",
        "permissions": [
            "projects.view",
            "knowledge_packs.view",
            "scripts.view",
            "scripts.create",
            "scripts.update",
            "workflows.view",
            "workflows.update",
            "versions.view",
            "versions.create",
            "content_versions.view",
            "content_versions.create",
            "approvals.create",
            "ai.view",
            "ai.generate",
            "prompt.manage",
            "production.view",
            "editorial_topics.view",
            "content_standards.view",
        ],
    },
    "Reviewer": {
        "description": "Reviews and approves or rejects content.",
        "permissions": [
            "projects.view",
            "knowledge_packs.view",
            "scripts.view",
            "workflows.view",
            "versions.view",
            "content_versions.view",
            "approvals.view",
            "approvals.approve",
            "approvals.reject",
            "approvals.review",
            "ai.view",
            "production.view",
            "editorial_topics.view",
            "content_standards.view",
        ],
    },
}

OWNER_ROLE_NAME = "Owner"
