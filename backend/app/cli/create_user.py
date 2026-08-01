"""Controlled CLI for creating the first (or additional) local users."""

from __future__ import annotations

import argparse
import getpass
import sys

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.schemas.auth import UserCreate
from app.services.user_service import DuplicateEmailError, create_user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Curionex Studio user securely. "
            "Password is prompted interactively and never printed."
        )
    )
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--first-name", required=True, help="First name")
    parser.add_argument("--last-name", required=True, help="Last name")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Ensure settings load (and surface JWT/DB misconfig early if needed).
    get_settings()

    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match.", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        return 1

    payload = UserCreate(
        email=args.email,
        password=password,
        first_name=args.first_name,
        last_name=args.last_name,
    )

    db = SessionLocal()
    try:
        user = create_user(db, payload)
    except DuplicateEmailError:
        print("A user with this email already exists.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Failed to create user: {exc.__class__.__name__}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Created user {user.email} ({user.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
