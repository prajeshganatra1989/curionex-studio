"""FastAPI application entrypoint for Curionex Studio."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.cors import configure_cors


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "API that powers Curionex Studio, a content production "
            "management platform for educational content creation."
        ),
    )
    configure_cors(application, settings)
    application.include_router(api_router)
    return application


app = create_app()
