# Knowledge Pack Section Catalog (M2F)

Centralized in `app/knowledge_packs/catalog.py`. Routes and services must not hard-code
section keys ad hoc.

| Key | Default title | Purpose |
|-----|---------------|---------|
| `research` | Research | Research and background information |
| `facts` | Facts | Verified factual information |
| `sources` | Sources | Sources and references used during research |
| `audience` | Audience | Intended audience information |
| `content_angle` | Content angle | Core angle or perspective of the content |
| `key_insights` | Key insights | Important insights and takeaways |
| `additional_context` | Additional context | Extra context that does not fit other sections |

Default positions are 1–7 in the order above.

New section types can be appended to the catalog in a future milestone; existing packs
would need a migration/backfill strategy at that time. M2F does not expose arbitrary
section creation via API.
