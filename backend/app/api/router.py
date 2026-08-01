"""Aggregate API routers for the application."""

from fastapi import APIRouter

from app.api.routes import (
    audit,
    auth,
    categories,
    content_versions,
    health,
    knowledge_packs,
    projects,
    rbac,
    scripts,
    tags,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(audit.router)
api_router.include_router(projects.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
api_router.include_router(knowledge_packs.project_packs_router)
api_router.include_router(knowledge_packs.packs_router)
api_router.include_router(content_versions.project_versions_router)
api_router.include_router(content_versions.versions_router)
api_router.include_router(content_versions.approvals_router)
api_router.include_router(scripts.project_scripts_router)
api_router.include_router(scripts.scripts_router)
