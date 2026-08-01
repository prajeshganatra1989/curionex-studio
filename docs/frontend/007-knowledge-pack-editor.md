# Knowledge Pack Research Workspace

## Route

`/projects/{projectId}/knowledge-packs/{knowledgePackId}`

Primary writing environment — one calm, vertically scrolling page.
Not a CRUD admin screen.

## Architecture

```
KnowledgePackEditor
├── Header (Back · SaveIndicator · Save · Generate Script)
├── SectionDrawer (mobile)
├── SectionNavigator (desktop sticky)
├── KnowledgePackSection × 7
│   ├── WordCounter
│   ├── CharacterCounter
│   └── inline error + Retry
└── ProgressSidebar (xl sticky)
    └── CompletionBadge × 7
```

Data flow:

1. `useKnowledgePack` → `GET /knowledge-packs/{id}` (includes sections)
2. Local draft map hydrated once from server content
3. Dirty keys = draft ≠ baseline
4. Save → `PATCH /knowledge-packs/{id}/sections/{section_key}` for dirty keys only

## Components

| Component | Role |
|-----------|------|
| `KnowledgePackEditor` | Workspace shell, query/save orchestration |
| `KnowledgePackSection` | Memoized section title, helper, textarea, counters |
| `SectionNavigator` | Sticky mini-nav with completion badges |
| `SectionDrawer` | Mobile navigator drawer |
| `ProgressSidebar` | Completion %, words, characters, reading time |
| `SaveIndicator` | Unsaved / Saving / Saved just now |
| `WordCounter` / `CharacterCounter` | Local metrics |
| `CompletionBadge` | ✔ / ○ |

## Save strategy

- Manual only — no autosave
- Save disabled until dirty
- Optimistic-safe: drafts never cleared on failure
- Successful sections advance baseline; failures keep text + Retry
- Toast on success / partial / total failure

## Navigation

- Desktop: sticky left navigator, smooth-scroll, IntersectionObserver highlight
- Mobile: list button → drawer navigator
- Browser find-in-page works on native textareas

## Progress (local only)

- Completion % = non-empty sections / 7
- Word + character totals from current drafts
- Reading time at 200 wpm
- Never invent values

## Performance

- Section editors and side panels wrapped in `memo`
- Draft updates skip no-op identical values
- Progress stats memoized from content map
- TanStack Query for pack/project load; targeted invalidation after save

## Generate Script

Navigates to `/projects/{projectId}/scripts` (placeholder). Does not generate content.
