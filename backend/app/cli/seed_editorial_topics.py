"""Idempotent Editorial Library seed — 100 evergreen topics."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.editorial.seed_catalog import EDITORIAL_SEED_SOURCE, SEED_TOPICS
from app.models.editorial import EditorialTopic


def seed_editorial_topics(db) -> dict[str, int]:
    """Insert missing seed topics by slug. Never updates existing rows."""
    existing = set(db.scalars(select(EditorialTopic.slug)).all())
    created = 0
    skipped = 0
    for item in SEED_TOPICS:
        slug = item["slug"]
        if slug in existing:
            skipped += 1
            continue
        db.add(
            EditorialTopic(
                slug=slug,
                title=item["title"],
                description=item.get("description"),
                category=item["category"],
                status="idea",
                difficulty=item["difficulty"],
                evergreen_score=item["evergreen_score"],
                curiosity_score=item["curiosity_score"],
                viral_potential=item["viral_potential"],
                estimated_duration_seconds=item["estimated_duration_seconds"],
                target_audience=item.get("target_audience"),
                source=EDITORIAL_SEED_SOURCE,
                notes=item.get("notes"),
                is_featured=bool(item.get("is_featured", False)),
            )
        )
        existing.add(slug)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "total_seed": len(SEED_TOPICS)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently seed 100 evergreen editorial topics."
    )
    parser.parse_args(argv)
    get_settings()
    db = SessionLocal()
    try:
        result = seed_editorial_topics(db)
    except Exception as exc:  # noqa: BLE001
        print(
            f"Failed to seed editorial topics: {exc.__class__.__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        db.close()

    print(
        "Editorial seed complete: "
        f"created={result['created']} skipped={result['skipped']} "
        f"catalog={result['total_seed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
