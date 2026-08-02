# Frontend — AI Script Drafting

## Generate AI Draft (document-level)

From a Script Document editor, **Generate AI Draft** opens a dialog for that document type (Discovery Brief, Story Spine, or Master Script).

Dialog shows model (OpenAI only; blank = default), language, tone, target duration, and WPM for Master Script. Prerequisites are loaded via `ai-prerequisites`; missing stages disable submit.

Warning: AI content is unverified; nothing is written until review + apply; apply does not create a Content Version.

Submission uses an `idempotency_key` and disables duplicate clicks. Job statuses poll until terminal; cancel while queued/running.

## Dirty-state Save before Generate

If the workspace has unsaved edits, the dialog shows a dirty hint and the primary action becomes **Save and Generate**. It saves first, then queues the job so fingerprints and prerequisites use latest content. Save failure blocks generation.

## Review panel

After completion, the review panel shows:

- Purpose / applied status  
- Generation warnings  
- Claims requiring verification (**HUMAN CHECK REQUIRED**)  
- Stale-input warning when upstream fingerprints diverge  
- Current vs generated plain-text preview (client conversion mirrors backend)  
- Master Script metrics (word count vs ±10% target, duration, keywords, editor notes)

Apply strategies: `reject_if_non_empty` (default), `replace`, `append`. Replace/append require confirmation when content exists. Successful apply refreshes only that document so dirty drafts on other documents are preserved.

## Guided pipeline

`ScriptAiPipelinePanel` lists stages Discovery Brief → Story Spine → Master Script with ready / blocked / in progress / complete status. Blocked stages disable Generate until prior documents have started content. A **Next action** CTA suggests the next generate/continue/regenerate step. Copy states drafts are never auto-applied.

Step-by-step generation from a single editor and guided pipeline both use the same dialog + review flow.

## Generation history

AI Generation History supports filters for `script_id`, `document_type` (script draft types), `purpose` (including the three `script.*.draft` codes), project, and applied status. Rows show document type when present; Open Draft / review remains available when a script document is linked.
