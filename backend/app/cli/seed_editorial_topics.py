"""Idempotent Production Editorial Catalog seed + curation apply."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.editorial.constants import TOPIC_STATUS_ARCHIVED, TOPIC_STATUS_IDEA
from app.editorial.seed_catalog import (
    CURATION_ARCHIVE_SLUGS,
    EDITORIAL_SEED_SOURCE,
    SEED_TOPICS,
    SLUG_RENAME_MAP,
)
from app.models.editorial import EditorialTopic


def _apply_fields(topic: EditorialTopic, item: dict) -> None:
    topic.title = item["title"]
    topic.description = item.get("description")
    topic.category = item["category"]
    topic.difficulty = item["difficulty"]
    topic.evergreen_score = item["evergreen_score"]
    topic.curiosity_score = item["curiosity_score"]
    topic.viral_potential = item["viral_potential"]
    topic.estimated_duration_seconds = item["estimated_duration_seconds"]
    topic.target_audience = item.get("target_audience")
    topic.source = EDITORIAL_SEED_SOURCE
    topic.notes = item.get("notes")
    topic.is_featured = bool(item.get("is_featured", False))
    topic.priority = item["priority"]
    topic.production_wave = int(item["production_wave"])


def seed_editorial_topics(db) -> dict[str, int]:
    """Apply production catalog: rename, archive, upsert by slug."""
    renamed = 0
    for old_slug, new_slug in SLUG_RENAME_MAP.items():
        topic = db.scalars(
            select(EditorialTopic).where(EditorialTopic.slug == old_slug)
        ).first()
        if topic is None:
            continue
        existing_new = db.scalars(
            select(EditorialTopic).where(EditorialTopic.slug == new_slug)
        ).first()
        if existing_new is not None and existing_new.id != topic.id:
            topic.status = TOPIC_STATUS_ARCHIVED
            topic.notes = (
                f"{topic.notes or ''}\nArchived during rename; "
                f"canonical slug is {new_slug}."
            ).strip()
        else:
            topic.slug = new_slug
            renamed += 1

    archived = 0
    for slug in CURATION_ARCHIVE_SLUGS:
        topic = db.scalars(
            select(EditorialTopic).where(EditorialTopic.slug == slug)
        ).first()
        if topic is None:
            continue
        if topic.status != TOPIC_STATUS_ARCHIVED:
            topic.status = TOPIC_STATUS_ARCHIVED
            archived += 1

    by_slug = {
        topic.slug: topic
        for topic in db.scalars(select(EditorialTopic)).all()
    }
    created = 0
    updated = 0
    for item in SEED_TOPICS:
        slug = item["slug"]
        topic = by_slug.get(slug)
        if topic is None:
            topic = EditorialTopic(slug=slug, status=TOPIC_STATUS_IDEA)
            _apply_fields(topic, item)
            db.add(topic)
            by_slug[slug] = topic
            created += 1
        else:
            _apply_fields(topic, item)
            if topic.status == TOPIC_STATUS_ARCHIVED:
                # Catalog topics should stay active unless intentionally archived.
                topic.status = TOPIC_STATUS_IDEA
            updated += 1

    db.commit()
    return {
        "created": created,
        "updated": updated,
        "renamed": renamed,
        "archived": archived,
        "skipped": 0,
        "total_seed": len(SEED_TOPICS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply the Production Editorial Catalog (100 curated topics)."
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
        "Editorial catalog curation complete: "
        f"created={result['created']} updated={result['updated']} "
        f"renamed={result['renamed']} archived={result['archived']} "
        f"catalog={result['total_seed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
