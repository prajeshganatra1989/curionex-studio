"""Seed the initial RBAC permission and role catalog."""

from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.rbac_service import seed_rbac_catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently seed RBAC permissions and roles."
    )
    parser.parse_args(argv)
    get_settings()

    db = SessionLocal()
    try:
        result = seed_rbac_catalog(db)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to seed RBAC: {exc.__class__.__name__}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(
        "RBAC seed complete: "
        f"permissions={result['permissions_created']} "
        f"roles={result['roles_created']} "
        f"grants={result['grants_created']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
