"""Idempotent Curionex Content Standard v1 seed."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.rbac import UserRole
from app.models.user import User
from app.rbac.catalog import OWNER_ROLE_NAME
from app.services.content_standard_service import ensure_content_standard_v1
from app.services.rbac_service import get_role_by_name


def _resolve_actor(db) -> User | None:
    owner_role = get_role_by_name(db, OWNER_ROLE_NAME)
    if owner_role is None:
        return db.scalars(select(User).limit(1)).first()
    link = db.scalars(
        select(UserRole).where(UserRole.role_id == owner_role.id).limit(1)
    ).first()
    if link is None:
        return db.scalars(select(User).limit(1)).first()
    return db.get(User, link.user_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently seed Curionex Content Standard v1."
    )
    parser.parse_args(argv)
    get_settings()

    db = SessionLocal()
    try:
        actor = _resolve_actor(db)
        standard = ensure_content_standard_v1(db, actor=actor)
    except Exception as exc:  # noqa: BLE001
        print(
            f"Failed to seed content standard: {exc.__class__.__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        db.close()

    print(
        "Content standard seed complete: "
        f"id={standard.id} version={standard.version} status={standard.status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
