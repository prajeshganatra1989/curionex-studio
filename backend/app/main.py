"""FastAPI application entrypoint for Curionex Studio."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "API that powers Curionex Studio, a content production "
            "management platform for educational content creation."
        ),
    )
    application.include_router(api_router)
    return application


app = create_app()
