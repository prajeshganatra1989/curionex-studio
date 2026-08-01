"""Request context helpers for audit logging."""

from dataclasses import dataclass
from ipaddress import ip_address

from fastapi import Request


@dataclass(frozen=True, slots=True)
class RequestAuditContext:
    """Safe subset of request context for audit events."""

    ip_address: str | None
    user_agent: str | None


def _normalize_ip(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return str(ip_address(raw))
    except ValueError:
        # e.g. Starlette TestClient host "testclient"
        return None


def extract_request_audit_context(request: Request) -> RequestAuditContext:
    """Extract IP and User-Agent only — never headers with credentials."""
    raw_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    if user_agent is not None:
        user_agent = user_agent[:512]
    return RequestAuditContext(
        ip_address=_normalize_ip(raw_ip),
        user_agent=user_agent,
    )
