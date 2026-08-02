# Topic Seeding

Idempotent seed of **100** curated evergreen topics.

```bash
cd backend
source .venv/bin/activate
python -m app.cli.seed_editorial_topics
```

## Catalog

- Source marker: `curionex-evergreen-v1`
- Categories (10 topics each): Human Brain, Psychology, Space, Earth, Science, Technology, History, Animals, Human Body, Biology
- Defined in `app/editorial/seed_catalog.py`

## Idempotency

Existing rows matched by **slug** are skipped. Seed never updates existing topics.
