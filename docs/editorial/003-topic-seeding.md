# Topic Seeding

Idempotent **Production Editorial Catalog** seed of **100** curated topics.

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.cli.seed_editorial_topics
```

## Catalog

- Source marker: `curionex-production-catalog-v1`
- Defined in `app/editorial/seed_catalog.py`
- Includes `priority` (A/B/C) and `production_wave` (1–4)
- Audit decisions applied: title/slug improvements, merges, removals + replacements

## Idempotency

The seed **upserts** by slug:

1. Renames legacy slugs (`SLUG_RENAME_MAP`)
2. Soft-archives REMOVE/MERGE slugs (`CURATION_ARCHIVE_SLUGS`)
3. Creates missing catalog rows or updates existing ones (scores, priority, wave, copy)

See [006-production-catalog.md](./006-production-catalog.md).
