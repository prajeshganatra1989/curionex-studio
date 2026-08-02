# Production Editorial Catalog

The Editorial Library is curated into the **Curionex Production Catalog** (`curionex-production-catalog-v1`).

Source of truth for curation decisions:

- [005-editorial-audit.md](./005-editorial-audit.md)
- [editorial_audit.csv](./editorial_audit.csv)

## Final topic rules

Every active catalog topic must have:

| Field | Rule |
|-------|------|
| Title | Why / How / What preferred; no vague noun titles |
| Slug | Unique kebab-case; updated when titles improve |
| Category | One of the 10 editorial categories |
| Difficulty | `easy` / `medium` / `hard` |
| Evergreen score | 0–100 (audit score) |
| Curiosity score | 0–100 (audit score) |
| Priority | `A` / `B` / `C` (required) |
| Production wave | `1`–`4` (required) |
| Estimated duration | 15–180 seconds (Shorts target 45–60) |
| Status | Lifecycle status (`idea` default for seed) |

Soft archive only — never hard-delete catalog rows.

## Priority rules

| Tier | Meaning | Production use |
|------|---------|----------------|
| **A** | Flagship Shorts — high evergreen + curiosity, reliable claims | Film first within Wave 1–2 |
| **B** | Solid library depth | Standard queue |
| **C** | Contested claims, weak brand fit, or needs rewrite | Deprioritize / fix before filming |

No active topic may omit priority.

## Wave rules

Topics are ordered by priority (A→B→C), then combined evergreen+curiosity score, then title.

| Wave | Contents |
|------|----------|
| **1** | Top 25 Tier A |
| **2** | Next 25 |
| **3** | Next 25 |
| **4** | Remaining |

Production Mode shows:

- Wave 1 remaining (idea / planned / in_progress)
- Wave 2 remaining
- Approved in current wave (`project_created`)
- Remaining in current wave

Current wave = lowest wave with remaining topics.

## Editorial standards

1. Apply audit KEEP / IMPROVE TITLE / MERGE / REMOVE before seeding.
2. IMPROVE TITLE updates both `title` and `slug`.
3. MERGE preserves one canonical topic; archive the near-duplicate; replace with a stronger category peer if needed to keep 100 active ideas.
4. REMOVE archives rejected topics and inserts stronger replacements in the same category.
5. Do not auto-create Knowledge Packs from topics.
6. Prefer honesty over clickbait when claims are contested (hedge in description/notes).

## Apply catalog

```bash
cd backend
alembic upgrade head
python -m app.cli.seed_editorial_topics
```

The seed is **idempotent upsert**: renames legacy slugs, archives REMOVE/MERGE slugs, and updates scores / priority / wave on every run.

## Related

- [001-editorial-library.md](./001-editorial-library.md)
- [002-topic-lifecycle.md](./002-topic-lifecycle.md)
- [003-topic-seeding.md](./003-topic-seeding.md)
- [004-create-project-from-topic.md](./004-create-project-from-topic.md)
- [005-editorial-audit.md](./005-editorial-audit.md)
