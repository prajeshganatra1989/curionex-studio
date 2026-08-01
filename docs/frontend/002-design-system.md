# Curionex Design System

## Surfaces

| Token | Role |
|-------|------|
| `--background` | App canvas (near black) |
| `--surface` | Sidebar / cards |
| `--surface-elevated` | Raised panels |
| `--surface-hover` | Interactive hover |
| `--border` / `--border-strong` | Hairline separators |

## Brand

| Token | Role |
|-------|------|
| `--brand-yellow` | Gradient start |
| `--brand-amber` | Mid accent |
| `--brand-orange` | Attention / active nav |
| `--brand-gradient` | Primary CTA fill |

Orange guides attention — it should not flood every surface.

## Typography

- Geist Sans for UI
- Geist Mono for codes / shortcuts
- Strong hierarchy: page title → section → body → muted meta
- Tabular numerals on metrics

## Spacing & radius

- Compact SaaS density
- `--radius` ≈ 12px panels (not pill-heavy)

## Shadows / glow

- Soft panel shadow
- Subtle warm brand glow on active nav and primary CTA

## Status colours

| Tone | Examples |
|------|----------|
| success | approved, completed, active |
| warning | pending, in_review |
| danger | rejected |
| info | draft |
| muted | archived |

## Component principles

- Prefer composition over one giant page component
- Extract only repeated patterns
- Communicate state with text + colour (not colour alone)
