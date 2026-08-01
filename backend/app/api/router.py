"""Aggregate API routers for the application."""

from fastapi import APIRouter

from app.api.routes import auth, health, rbac

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
