"""Aggregate API routers for the application."""

from fastapi import APIRouter

from app.api.routes import audit, auth, categories, health, projects, rbac, tags

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(audit.router)
api_router.include_router(projects.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
