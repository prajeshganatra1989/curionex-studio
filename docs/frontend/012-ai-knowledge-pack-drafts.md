# Frontend — AI Knowledge Pack Drafts

## Generate AI Draft

From the Knowledge Pack Editor, open **Generate AI Draft**.

Dialog shows project/topic context, OpenAI model, audience/language/depth, and a warning that AI research and sources require human verification.

Submission uses an `idempotency_key` and disables duplicate clicks.

## Job progress

Statuses: queued → running → completed | failed | cancelled.

Polling via TanStack Query stops on terminal states. Cancel is available while queued/running. No fake progress percentages.

## Draft review

Sections are reviewed individually with Apply checkboxes, current vs generated previews, and conflict indicators.

Sources display **UNVERIFIED — HUMAN CHECK REQUIRED**.

Default conflict strategy: `reject_if_non_empty`. Replace/append require confirmation.

## Apply

Successful apply refreshes only selected sections so unsaved edits on other sections are preserved. Generation history retains the draft.

## Generation history

Lists purpose, tokens, estimated cost, applied status, and an Open Draft action when a Knowledge Pack is linked.
