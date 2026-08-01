# Knowledge Pack Editor

## Route

`/projects/{projectId}/knowledge-packs/{knowledgePackId}`

This is the primary research writing workspace — one continuous scrolling page
(no tabs, no accordion routes).

## Layout

| Viewport | Layout |
|----------|--------|
| Desktop (`xl`) | Left section nav · Center editors · Right progress |
| Tablet (`lg`) | Left section nav · Center editors (progress hidden) |
| Mobile | Horizontal section nav under header · single column editors |

## Sections (fixed order)

1. Research  
2. Facts  
3. Sources  
4. Audience  
5. Content Angle  
6. Key Insights  
7. Additional Context  

Each section shows title, description, plain-text editor, character count, and
last-saved time. Empty sections show writing guidance (not AI).

## APIs

| Action | Endpoint |
|--------|----------|
| Load pack + sections | `GET /knowledge-packs/{id}` |
| Save section content | `PATCH /knowledge-packs/{id}/sections/{section_key}` |
| Project header context | `GET /projects/{id}` |

No duplicate save endpoints. Only modified sections are PATCHed.

## Save strategy

- Manual Save only (top-right). No autosave.
- Dirty indicator: `Unsaved changes` / `Saving...` / `Saved {relative time}`
- Optimistic UI is conservative: local drafts always retained on failure
- Successful section responses update baselines; failed sections keep drafts +
  inline error with Retry

## Progress (local)

Computed from current draft content — never invented:

- Completion % = sections with non-whitespace content / 7
- Per-section Done / Empty
- Word count across all sections
- Estimated reading time at 200 wpm

## Navigation

Left (or horizontal on mobile) mini-nav smooth-scrolls to section anchors and
highlights the section currently in view (IntersectionObserver).

## Entry points

- Create Knowledge Pack → navigates into the editor
- Project Home pack rows → editor
- Project Knowledge Packs list (`/projects/{id}/packs`) → editor
