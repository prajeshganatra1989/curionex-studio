"""Health check routes."""

from fastapi import APIRouter, HTTPException, status

from app.db.session import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return process health without touching PostgreSQL."""
    return {
        "status": "ok",
        "service": "curionex-studio-api",
    }


@router.get("/health/db")
def health_db() -> dict[str, str]:
    """Verify PostgreSQL connectivity with a lightweight probe."""
    try:
        check_database_connection()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "unavailable",
            },
        ) from None

    return {
        "status": "ok",
        "database": "connected",
    }
