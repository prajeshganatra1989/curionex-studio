"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAiGeneration, useApplyScriptAiDraft } from "@/lib/ai/hooks";
import type {
  ScriptAiConflictStrategy,
  ScriptAiDocumentType,
} from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";
import type { ScriptDocument } from "@/lib/api/types";
import { DOCUMENT_BY_TYPE } from "@/lib/scripts/documents";
import {
  claimsRequiringVerification,
  parseScriptDraft,
  scriptDraftToPlainText,
  targetWordRange,
} from "@/lib/scripts/draft";
import { countWords } from "@/lib/scripts/metrics";

const CONFLICT_STRATEGY_OPTIONS: {
  value: ScriptAiConflictStrategy;
  label: string;
}[] = [
  { value: "reject_if_non_empty", label: "Reject if document has content (safest)" },
  { value: "replace", label: "Replace existing content" },
  { value: "append", label: "Append after existing content" },
];

type ScriptAiDraftReviewPanelProps = {
  scriptId: string;
  documentType: ScriptAiDocumentType;
  generationId: string;
  /** Current (possibly unsaved) editor content for this document. */
  currentContent: string;
  onApplied: (result: {
    document: ScriptDocument;
    generationId: string;
    staleInput: boolean;
  }) => void;
  onClose: () => void;
};

export function ScriptAiDraftReviewPanel({
  scriptId,
  documentType,
  generationId,
  currentContent,
  onApplied,
  onClose,
}: ScriptAiDraftReviewPanelProps) {
  const meta = DOCUMENT_BY_TYPE[documentType];
  const generationQuery = useAiGeneration(generationId);
  const applyDraft = useApplyScriptAiDraft(scriptId, documentType);

  const parsed = useMemo(
    () =>
      parseScriptDraft(
        documentType,
        generationQuery.data?.structured_output,
      ),
    [documentType, generationQuery.data?.structured_output],
  );

  const generatedText = useMemo(
    () => (parsed ? scriptDraftToPlainText(parsed) : ""),
    [parsed],
  );

  const claims = useMemo(
    () => (parsed ? claimsRequiringVerification(parsed) : []),
    [parsed],
  );

  const alreadyApplied = Boolean(
    generationQuery.data?.applied_sections?.includes(documentType) ||
      generationQuery.data?.applied_at,
  );

  const [conflictStrategy, setConflictStrategy] =
    useState<ScriptAiConflictStrategy>("reject_if_non_empty");
  const [pendingConfirm, setPendingConfirm] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  const hasExistingContent = currentContent.trim().length > 0;
  const staleInput = generationQuery.data?.stale_input === true;

  const masterMeta = useMemo(() => {
    if (!parsed || parsed.documentType !== "master_script") return null;
    const draft = parsed.draft;
    const narrationWords = countWords(draft.narration);
    const targetDuration = Number.parseInt(
      String(
        generationQuery.data?.input_variables?.target_duration_seconds ?? "60",
      ),
      10,
    );
    const rawWpm =
      generationQuery.data?.input_variables?.target_words_per_minute;
    const targetWpm = Number.parseInt(String(rawWpm ?? "150"), 10);
    const range = targetWordRange(
      Number.isFinite(targetDuration) ? targetDuration : 60,
      Number.isFinite(targetWpm) && targetWpm > 0 ? targetWpm : 150,
    );
    const durationMismatch =
      !draft.quality_checks.duration_target_met ||
      narrationWords < range.low ||
      narrationWords > range.high;
    return {
      draft,
      narrationWords,
      range,
      durationMismatch,
      targetDuration: Number.isFinite(targetDuration) ? targetDuration : 60,
    };
  }, [parsed, generationQuery.data?.input_variables]);

  async function doApply() {
    setApplyError(null);
    try {
      const result = await applyDraft.mutateAsync({
        generationId,
        payload: { conflict_strategy: conflictStrategy },
      });
      setPendingConfirm(false);
      onApplied({
        document: result.document as ScriptDocument,
        generationId: result.generation_id,
        staleInput: result.stale_input,
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const data = error.data as { message?: string } | undefined;
        setApplyError(
          data?.message ??
            error.detail ??
            "Document already contains content.",
        );
      } else {
        setApplyError(
          error instanceof ApiError ? error.detail : "Unable to apply draft.",
        );
      }
    }
  }

  function handleApplyClick() {
    if (
      conflictStrategy !== "reject_if_non_empty" &&
      hasExistingContent
    ) {
      setPendingConfirm(true);
      return;
    }
    void doApply();
  }

  if (generationQuery.isLoading) {
    return <LoadingSkeleton className="h-64" />;
  }

  if (generationQuery.isError || !generationQuery.data) {
    return (
      <ErrorState message="Unable to load the AI draft. Try opening it again from Generation History." />
    );
  }

  const generation = generationQuery.data;

  if (!parsed || !generatedText.trim()) {
    return (
      <ErrorState message="This generation has no structured draft to review." />
    );
  }

  const warnings = generation.warnings ?? [];

  return (
    <div className="space-y-5" data-testid="script-ai-draft-review-panel">
      <div
        className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">Review before applying.</p>
        <p className="mt-0.5 text-muted-foreground">
          AI-generated content requires human review and claim verification.
          Applying updates only this document — it does not create a Content
          Version.
        </p>
      </div>

      {staleInput ? (
        <div
          className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
          role="alert"
          data-testid="script-ai-stale-warning"
        >
          <p className="font-medium">Input may be stale.</p>
          <p className="mt-0.5 text-muted-foreground">
            Upstream documents or Knowledge Pack content changed since this
            draft was generated. Consider regenerating before applying.
          </p>
        </div>
      ) : null}

      <dl className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
        <div>
          <dt className="uppercase tracking-wide">Document</dt>
          <dd className="text-foreground">{meta.title}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Purpose</dt>
          <dd className="text-foreground">{generation.purpose ?? "—"}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Status</dt>
          <dd className="flex items-center gap-1.5 text-foreground">
            {alreadyApplied ? <StatusBadge status="completed" /> : "Not applied"}
          </dd>
        </div>
      </dl>

      {warnings.length > 0 ? (
        <div
          className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
          data-testid="script-ai-warnings"
        >
          <p className="font-medium">Warnings from the model</p>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {claims.length > 0 ? (
        <div
          className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
          data-testid="script-ai-claims"
        >
          <p className="font-medium">
            Claims requiring verification — HUMAN CHECK REQUIRED
          </p>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {claims.map((claim, index) => (
              <li key={index}>{claim}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {masterMeta ? (
        <div
          className="space-y-2 rounded-xl border border-border/70 p-4 text-sm"
          data-testid="script-ai-master-meta"
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Master Script metrics
          </p>
          <dl className="grid gap-2 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-muted-foreground">Word count</dt>
              <dd className="tabular-nums text-foreground">
                {masterMeta.narrationWords}{" "}
                <span className="text-muted-foreground">
                  (target {masterMeta.range.low}–{masterMeta.range.high})
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Est. duration</dt>
              <dd className="tabular-nums text-foreground">
                {masterMeta.draft.estimated_duration_seconds}s{" "}
                <span className="text-muted-foreground">
                  (target {masterMeta.targetDuration}s)
                </span>
              </dd>
            </div>
          </dl>
          {masterMeta.durationMismatch ? (
            <p
              className="text-xs font-medium text-warning"
              data-testid="script-ai-duration-mismatch"
            >
              Duration / word-count target may not be met. Review narration
              length before applying.
            </p>
          ) : null}
          {masterMeta.draft.on_screen_keywords.length > 0 ? (
            <div>
              <p className="text-xs text-muted-foreground">On-screen keywords</p>
              <p className="text-foreground">
                {masterMeta.draft.on_screen_keywords.join(", ")}
              </p>
            </div>
          ) : null}
          {masterMeta.draft.editor_notes.length > 0 ? (
            <div>
              <p className="text-xs text-muted-foreground">Editor notes</p>
              <ul className="mt-0.5 list-inside list-disc text-foreground">
                {masterMeta.draft.editor_notes.map((note, index) => (
                  <li key={index}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Current
          </p>
          <pre
            className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
            data-testid="script-ai-current-content"
          >
            {currentContent.trim() ? currentContent : "(empty)"}
          </pre>
          {hasExistingContent ? (
            <span className="mt-1 inline-block rounded-md border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs text-warning">
              Has existing content
            </span>
          ) : null}
        </div>
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Generated
          </p>
          <pre
            className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-brand-orange/30 bg-surface/60 px-3 py-2 text-xs text-foreground"
            data-testid="script-ai-generated-content"
          >
            {generatedText}
          </pre>
        </div>
      </div>

      <Field
        label="If this document already has content"
        htmlFor="script-ai-conflict-strategy"
      >
        <TextSelect
          id="script-ai-conflict-strategy"
          value={conflictStrategy}
          onChange={(event) => {
            setConflictStrategy(
              event.target.value as ScriptAiConflictStrategy,
            );
            setPendingConfirm(false);
          }}
        >
          {CONFLICT_STRATEGY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </TextSelect>
      </Field>

      {applyError ? (
        <div
          className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
          data-testid="script-ai-apply-error"
        >
          {applyError}
        </div>
      ) : null}

      {pendingConfirm ? (
        <div
          className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
          data-testid="script-ai-confirm"
        >
          <p>
            This will{" "}
            {conflictStrategy === "replace" ? "replace" : "append to"} existing
            content in <strong>{meta.title}</strong>. Continue?
          </p>
          <div className="mt-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setPendingConfirm(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void doApply()}
              loading={applyDraft.isPending}
              data-testid="script-ai-confirm-apply"
            >
              Confirm apply
            </Button>
          </div>
        </div>
      ) : null}

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="secondary" onClick={onClose}>
          Close
        </Button>
        <Button
          type="button"
          onClick={handleApplyClick}
          loading={applyDraft.isPending}
          disabled={applyDraft.isPending || pendingConfirm}
          data-testid="script-ai-apply-button"
        >
          Apply to {meta.title}
        </Button>
      </div>
    </div>
  );
}
