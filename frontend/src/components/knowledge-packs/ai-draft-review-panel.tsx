"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAiGeneration, useApplyKnowledgePackAiDraft } from "@/lib/ai/hooks";
import { ApiError } from "@/lib/api/client";
import {
  KNOWLEDGE_PACK_APPLYABLE_SECTIONS,
  type KnowledgePackAiDraftConflictDetail,
  type KnowledgePackApplyableSection,
  type KnowledgePackConflictStrategy,
} from "@/lib/ai/types";
import {
  draftSectionIsEmpty,
  draftSectionToPlainText,
  parseKnowledgePackDraft,
} from "@/lib/knowledge-packs/draft";
import { SECTION_BY_KEY } from "@/lib/knowledge-packs/sections";

const CONFLICT_STRATEGY_OPTIONS: {
  value: KnowledgePackConflictStrategy;
  label: string;
}[] = [
  { value: "reject_if_non_empty", label: "Reject if section has content (safest)" },
  { value: "replace_selected", label: "Replace existing content" },
  { value: "append_selected", label: "Append after existing content" },
];

function sectionTitle(key: string): string {
  return SECTION_BY_KEY[key as KnowledgePackApplyableSection]?.title ?? key;
}

type AiDraftReviewPanelProps = {
  knowledgePackId: string;
  generationId: string;
  /** Current (possibly unsaved) editor content, keyed by section_key. */
  currentSectionContents: Record<string, string>;
  onApplied: (result: { appliedSections: string[] }) => void;
  onClose: () => void;
};

export function AiDraftReviewPanel({
  knowledgePackId,
  generationId,
  currentSectionContents,
  onApplied,
  onClose,
}: AiDraftReviewPanelProps) {
  const generationQuery = useAiGeneration(generationId);
  const applyDraft = useApplyKnowledgePackAiDraft(knowledgePackId);

  const draft = useMemo(
    () => parseKnowledgePackDraft(generationQuery.data?.structured_output),
    [generationQuery.data?.structured_output],
  );

  const alreadyApplied = useMemo(
    () => new Set(generationQuery.data?.applied_sections ?? []),
    [generationQuery.data?.applied_sections],
  );

  const [selected, setSelected] = useState<Set<KnowledgePackApplyableSection>>(
    new Set(),
  );
  const [conflictStrategy, setConflictStrategy] =
    useState<KnowledgePackConflictStrategy>("reject_if_non_empty");
  const [pendingConfirm, setPendingConfirm] = useState<{
    sections: KnowledgePackApplyableSection[];
    conflicts: string[];
  } | null>(null);
  const [applyError, setApplyError] = useState<{
    message: string;
    conflicts: string[];
  } | null>(null);

  const initializedRef = useRef(false);
  useEffect(() => {
    if (initializedRef.current || !draft) return;
    initializedRef.current = true;
    const initial = new Set<KnowledgePackApplyableSection>();
    for (const key of KNOWLEDGE_PACK_APPLYABLE_SECTIONS) {
      if (!draftSectionIsEmpty(key, draft) && !alreadyApplied.has(key)) {
        initial.add(key);
      }
    }
    setSelected(initial);
  }, [draft, alreadyApplied]);

  function toggleSection(key: KnowledgePackApplyableSection) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function conflictsFor(keys: KnowledgePackApplyableSection[]): string[] {
    return keys.filter(
      (key) => (currentSectionContents[key] ?? "").trim().length > 0,
    );
  }

  async function doApply(keys: KnowledgePackApplyableSection[]) {
    setApplyError(null);
    try {
      const result = await applyDraft.mutateAsync({
        generationId,
        payload: { sections: keys, conflict_strategy: conflictStrategy },
      });
      setPendingConfirm(null);
      onApplied({ appliedSections: result.applied_sections });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const data = error.data as KnowledgePackAiDraftConflictDetail | undefined;
        setApplyError({
          message: data?.message ?? error.detail,
          conflicts: data?.conflicts ?? [],
        });
      } else {
        setApplyError({
          message:
            error instanceof ApiError ? error.detail : "Unable to apply draft.",
          conflicts: [],
        });
      }
    }
  }

  function handleApplyClick() {
    const keys = Array.from(selected);
    if (keys.length === 0) return;
    const conflicts = conflictsFor(keys);
    if (conflictStrategy !== "reject_if_non_empty" && conflicts.length > 0) {
      setPendingConfirm({ sections: keys, conflicts });
      return;
    }
    void doApply(keys);
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

  if (!draft) {
    return <ErrorState message="This generation has no structured draft to review." />;
  }

  return (
    <div className="space-y-5" data-testid="ai-draft-review-panel">
      <div
        className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">Review before applying.</p>
        <p className="mt-0.5 text-muted-foreground">
          AI-generated content requires review and source verification. Nothing
          here has been fact-checked.
        </p>
      </div>

      <dl className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
        <div>
          <dt className="uppercase tracking-wide">Purpose</dt>
          <dd className="text-foreground">{generation.purpose ?? "—"}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Tokens</dt>
          <dd className="tabular-nums text-foreground">
            {generation.tokens_total ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Estimated cost</dt>
          <dd className="tabular-nums text-foreground">
            {generation.cost_usd != null ? `$${generation.cost_usd.toFixed(4)}` : "—"}
          </dd>
        </div>
      </dl>

      {draft.warnings.length > 0 ? (
        <div
          className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
          data-testid="ai-draft-warnings"
        >
          <p className="font-medium">Warnings from the model</p>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {draft.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="divide-y divide-border/70 rounded-xl border border-border/70">
        {KNOWLEDGE_PACK_APPLYABLE_SECTIONS.map((key) => {
          const meta = SECTION_BY_KEY[key];
          const generated = draftSectionToPlainText(key, draft);
          const current = currentSectionContents[key] ?? "";
          const hasConflict = current.trim().length > 0;
          const empty = generated.trim().length === 0;
          const applied = alreadyApplied.has(key);
          return (
            <div key={key} className="p-4" data-testid={`ai-draft-section-${key}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <label className="flex items-start gap-2.5">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={selected.has(key)}
                    disabled={empty}
                    onChange={() => toggleSection(key)}
                    aria-label={`Apply ${meta.title}`}
                  />
                  <span>
                    <span className="block text-sm font-medium text-foreground">
                      {meta.title}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {meta.description}
                    </span>
                  </span>
                </label>
                <div className="flex flex-wrap items-center justify-end gap-1.5">
                  {applied ? <StatusBadge status="completed" /> : null}
                  {hasConflict ? (
                    <span className="rounded-md border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs text-warning">
                      Has existing content
                    </span>
                  ) : null}
                </div>
              </div>

              {empty ? (
                <p className="mt-3 text-xs italic text-muted-foreground">
                  No content generated for this section.
                </p>
              ) : (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Current
                    </p>
                    <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground">
                      {current.trim() ? current : "(empty)"}
                    </pre>
                  </div>
                  <div>
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Generated
                    </p>
                    <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-brand-orange/30 bg-surface/60 px-3 py-2 text-xs text-foreground">
                      {generated}
                    </pre>
                    {key === "sources" ? (
                      <p className="mt-1 text-[11px] font-medium text-danger">
                        UNVERIFIED — HUMAN CHECK REQUIRED
                      </p>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <Field label="If a section already has content" htmlFor="ai-draft-conflict-strategy">
        <TextSelect
          id="ai-draft-conflict-strategy"
          value={conflictStrategy}
          onChange={(event) => {
            setConflictStrategy(event.target.value as KnowledgePackConflictStrategy);
            setPendingConfirm(null);
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
          data-testid="ai-draft-apply-error"
        >
          <p className="font-medium">{applyError.message}</p>
          {applyError.conflicts.length > 0 ? (
            <p className="mt-1 text-xs">
              Conflicting sections:{" "}
              {applyError.conflicts.map(sectionTitle).join(", ")}. Choose
              &quot;Replace&quot; or &quot;Append&quot;, or deselect them.
            </p>
          ) : null}
        </div>
      ) : null}

      {pendingConfirm ? (
        <div
          className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
          data-testid="ai-draft-confirm"
        >
          <p>
            This will{" "}
            {conflictStrategy === "replace_selected" ? "replace" : "append to"}{" "}
            existing content in:{" "}
            <strong>{pendingConfirm.conflicts.map(sectionTitle).join(", ")}</strong>.
            Continue?
          </p>
          <div className="mt-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setPendingConfirm(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void doApply(pendingConfirm.sections)}
              loading={applyDraft.isPending}
              data-testid="ai-draft-confirm-apply"
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
          disabled={selected.size === 0 || applyDraft.isPending || Boolean(pendingConfirm)}
          data-testid="ai-draft-apply-button"
        >
          Apply selected ({selected.size})
        </Button>
      </div>
    </div>
  );
}
