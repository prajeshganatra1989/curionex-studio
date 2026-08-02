# Curionex Content Standard — v0.23.0

**Status:** Active editorial source of truth  
**Seed version:** `1`  
**Table:** `content_standards`

## Purpose

Every generated script should feel like it was written by the same editorial team. The Curionex Content Standard is the **single, versioned** place for mission, voice, structure, fact policy, and quality criteria.

AI prompts **reference** the active standard. They must not duplicate editorial rules inline.

## Mission

Explain fascinating topics with clarity, curiosity and credibility.

## Target audience

General audience · 13+ · English-speaking · curious learners

## Story structure

Hook → Context → Explanation → Twist → Payoff → CTA

## Hook philosophy

- Create curiosity immediately.
- Never use misleading clickbait.
- The viewer should understand the promise within five seconds.

## Fact policy

- Never invent statistics or quotes.
- State uncertainty honestly.
- Distinguish theory from evidence.
- Prefer authoritative sources; avoid unsupported claims.

## Prompt integration

1. The active row (`status = active`) is loaded at render time.
2. `inject_content_standard_variables` adds:
   - `content_standard` — full formatted block
   - `content_standard_label` — e.g. `Curionex Content Standard v1`
   - derived `brand_voice` / `quality_requirements` for legacy templates
3. Job execution and dry-run validation always inject the **current** active standard, so activating a new version updates rendering without editing every prompt.

## APIs

| Method | Path | Permission |
|--------|------|------------|
| GET | `/content-standards` | `content_standards.view` |
| GET | `/content-standards/active` | `content_standards.view` |
| GET | `/content-standards/summary` | `content_standards.view` |
| GET | `/content-standards/{id}` | `content_standards.view` |
| POST | `/content-standards` | `content_standards.manage` |
| PATCH | `/content-standards/{id}` | `content_standards.manage` |
| POST | `/content-standards/{id}/activate` | `content_standards.manage` |
| POST | `/content-standards/{id}/archive` | `content_standards.manage` |

Only **one** standard may be `active`. Activation archives the previous active row.

## Audit

Logged actions (no generation logs):

- `content_standard.created`
- `content_standard.updated`
- `content_standard.activated`
- `content_standard.archived`

## Seed

```bash
cd backend && python -m app.cli.seed_content_standard
```

Also re-run RBAC seed so `content_standards.*` permissions exist on roles.

## Settings UI

**Settings → Editorial** shows the current standard, version badge, status, last updated, and a full preview. Version switching UI is reserved for a later release (API activate/archive already works).

## Related docs

- [020-editorial-bible-v1.md](./020-editorial-bible-v1.md) — **Curionex Editorial Bible v1.0** (full editorial OS; Founding Collection)
- [008-brand-voice.md](./008-brand-voice.md)
- [009-editorial-principles.md](./009-editorial-principles.md)
- [010-quality-checklist.md](./010-quality-checklist.md)
