# Script Workspace

## Routes

| Route | Purpose |
|-------|---------|
| `/projects/{projectId}/scripts` | Project script list, search, filters, New Script |
| `/projects/{projectId}/scripts/{scriptId}` | Production Script Workspace |

## Layout

```
ScriptWorkspace
├── ScriptHeader (Back · codes · status · Save · Create Version · workflow action)
├── SectionDrawer → ScriptDocumentNavigator (mobile)
├── ScriptDocumentNavigator (desktop)
├── ScriptDocumentEditor × 3 (Discovery Brief · Story Spine · Master Script)
└── Right column (xl)
    ├── ScriptProgressPanel
    ├── WorkflowPanel
    ├── KnowledgePackContextPanel
    └── VersionHistoryPanel
```

Tablet/mobile: right column opens in a modal; navigator becomes a drawer.

## Document architecture

One workspace route with three anchored editors. Drafts stay in local state while switching documents. Document types match the backend catalog:

- `discovery_brief`
- `story_spine`
- `master_script`

Plain text only. No HTML, rich text, or AI features.

## Save strategy

- Manual save only (no autosave)
- Dirty keys = draft ≠ baseline per document
- Save patches dirty documents via `PATCH /scripts/{id}/documents/{document_type}`
- Failures keep local text and expose Retry
- `SaveIndicator`: Unsaved changes · Saving… · Saved just now · Save failed
- Browser `beforeunload` + in-app leave dialog when dirty

## Knowledge Pack context

Reads `GET /knowledge-packs/{id}` when associated. Shows Research, Facts, Sources, Audience, Content Angle, Key Insights summaries. Does **not** copy pack text into ScriptDocuments. Workspace remains usable with no pack linked.

## Progress calculations

Local only — structure, not quality:

- Started: trimmed content non-empty
- Complete: trimmed length ≥ transparent thresholds (80 / 80 / 120 chars)
- Completion % = complete documents / 3
- Totals from current drafts

## Narration estimate

Master Script words ÷ configurable WPM (default **150**) → seconds. Displayed as `Estimated voiceover: N seconds`. Utility: `lib/scripts/metrics.ts`.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| ⌘/Ctrl + S | Save dirty documents |
| Alt + 1 | Discovery Brief |
| Alt + 2 | Story Spine |
| Alt + 3 | Master Script |

All actions remain available without shortcuts.
