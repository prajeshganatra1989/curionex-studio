"""CORS support for browser frontends (environment-configurable origins)."""

from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def configure_cors(application, settings: Settings) -> None:
    """Attach CORS middleware when CORS_ORIGINS is configured.

    Does not enable credentials with wildcard origins.
    """
    origins = settings.cors_origin_list
    if not origins:
        return

    allow_credentials = True
    if "*" in origins:
        # Browsers forbid credentials + wildcard; keep API usable without cookies.
        allow_credentials = False

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins if "*" not in origins else ["*"],
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
