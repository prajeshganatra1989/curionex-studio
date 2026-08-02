"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import {
  useAiGeneration,
  useApplyScriptQualitySuggestion,
} from "@/lib/ai/hooks";
import type {
  ScriptQualityPriorityIssue,
  ScriptQualityRecommendation,
} from "@/lib/ai/types";
import { SCRIPT_QUALITY_DIMENSIONS } from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";
import type { ScriptDocument } from "@/lib/api/types";
import {
  dimensionLabel,
  isIssueApplied,
  PACING_STATUS_LABELS,
  qualityReviewFromGeneration,
  recommendationLabel,
} from "@/lib/scripts/quality";
import { formatRelativeTime } from "@/lib/utils";

type ScriptQualityReviewViewProps = {
  scriptId: string;
  generationId: string;
  /** Optional header actions (e.g. back link). */
  headerActions?: ReactNode;
  onApplied?: (result: {
    document: ScriptDocument;
    generationId: string;
    issueId: string;
    staleInput: boolean;
  }) => void;
};

function AdvisoryBadge({
  action,
}: {
  action: ScriptQualityRecommendation;
}) {
  const tone =
    action === "revise"
      ? "border-danger/30 bg-danger/15 text-danger"
      : action === "ready_for_version"
        ? "border-info/30 bg-info/15 text-info"
        : "border-warning/30 bg-warning/15 text-warning";
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${tone}`}
      data-testid="script-quality-advisory-badge"
    >
      {recommendationLabel(action)}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const tone =
    severity === "critical" || severity === "high"
      ? "border-danger/30 bg-danger/15 text-danger"
      : severity === "medium"
        ? "border-warning/30 bg-warning/15 text-warning"
        : "border-border bg-surface-hover text-muted-foreground";
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium capitalize ${tone}`}
    >
      {severity}
    </span>
  );
}

export function ScriptQualityReviewView({
  scriptId,
  generationId,
  headerActions,
  onApplied,
}: ScriptQualityReviewViewProps) {
  const { toast } = useToast();
  const generationQuery = useAiGeneration(generationId);
  const applySuggestion = useApplyScriptQualitySuggestion(scriptId);

  const review = useMemo(
    () => qualityReviewFromGeneration(generationQuery.data),
    [generationQuery.data],
  );

  const [confirmIssue, setConfirmIssue] =
    useState<ScriptQualityPriorityIssue | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  const staleInput = generationQuery.data?.stale_input === true;

  async function doApply(issue: ScriptQualityPriorityIssue) {
    setApplyError(null);
    try {
      const result = await applySuggestion.mutateAsync({
        generationId,
        issueId: issue.id,
        payload: { strategy: "replace_excerpt" },
      });
      setConfirmIssue(null);
      toast({
        title: "Suggestion applied",
        description:
          "Master Script updated. Review the change before creating a version.",
        tone: "success",
      });
      onApplied?.({
        document: result.document as ScriptDocument,
        generationId: result.generation_id,
        issueId: result.issue_id,
        staleInput: result.stale_input,
      });
    } catch (error) {
      const detail =
        error instanceof ApiError
          ? error.detail
          : "Unable to apply suggestion.";
      setApplyError(detail);
      if (error instanceof ApiError && error.status === 409) {
        toast({
          title: "Could not apply suggestion",
          description: detail,
          tone: "error",
        });
      }
    }
  }

  if (generationQuery.isLoading) {
    return (
      <div className="space-y-4" data-testid="script-quality-review-loading">
        <LoadingSkeleton className="h-28" />
        <LoadingSkeleton className="h-64" />
      </div>
    );
  }

  if (generationQuery.isError || !generationQuery.data) {
    return (
      <ErrorState message="Unable to load this quality review. It may have been removed or you may not have access." />
    );
  }

  if (!review) {
    return (
      <ErrorState message="This generation has no structured quality review to display." />
    );
  }

  const generation = generationQuery.data;
  const metrics = review.deterministic_metrics;
  const pacing = review.pacing_analysis;

  return (
    <div className="space-y-6" data-testid="script-quality-review-view">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <AdvisoryBadge action={review.recommended_next_action} />
            <span className="rounded-md border border-border bg-surface-hover px-2 py-0.5 text-xs text-muted-foreground">
              {review.quality_band_label}
            </span>
            <span className="rounded-md border border-border bg-surface-hover px-2 py-0.5 text-xs capitalize text-muted-foreground">
              Confidence: {review.confidence}
            </span>
            {staleInput ? (
              <span
                className="rounded-md border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs font-medium text-warning"
                data-testid="script-quality-review-stale"
              >
                Stale input
              </span>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            Reviewed{" "}
            <time dateTime={generation.created_at}>
              {formatRelativeTime(generation.created_at)}
            </time>
          </p>
        </div>
        {headerActions}
      </div>

      <div
        className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">Advisory review — not an approval.</p>
        <p className="mt-0.5 text-muted-foreground">
          AI never marks a script as approved. Apply suggestions only after
          human judgment. Applying never creates a Content Version.
        </p>
      </div>

      {staleInput ? (
        <div
          className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
          role="alert"
          data-testid="script-quality-stale-banner"
        >
          <p className="font-medium">Master Script changed since this review.</p>
          <p className="mt-0.5 text-muted-foreground">
            Suggestions cannot be applied until you run a fresh quality review.
          </p>
        </div>
      ) : null}

      {review.warnings.length > 0 ? (
        <div
          className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
        >
          <p className="font-medium">Warnings</p>
          <ul className="mt-1 list-inside list-disc">
            {review.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <section
        className="rounded-xl border border-border/70 bg-surface/40 p-4"
        data-testid="script-quality-scorecard"
      >
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Overall score
            </p>
            <p className="text-4xl font-semibold tabular-nums text-foreground">
              {review.overall_score}
            </p>
            {review.model_overall_score != null &&
            review.model_overall_score !== review.overall_score ? (
              <p className="mt-1 text-xs text-muted-foreground">
                Model score was {review.model_overall_score}; displayed score is
                server-calculated from weighted dimensions.
              </p>
            ) : null}
          </div>
          <div className="max-w-xl text-sm text-muted-foreground">
            {review.summary || "No summary provided."}
          </div>
        </div>
      </section>

      <section data-testid="script-quality-dimensions">
        <h2 className="mb-3 text-sm font-semibold text-foreground">
          Dimensions
        </h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {SCRIPT_QUALITY_DIMENSIONS.map((key) => {
            const dim = review.dimensions[key];
            if (!dim) return null;
            return (
              <li
                key={key}
                className="rounded-lg border border-border/60 bg-background/40 p-3"
                data-testid={`script-quality-dimension-${key}`}
              >
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground">
                    {dimensionLabel(key)}
                  </span>
                  <span className="tabular-nums text-sm text-foreground">
                    {dim.score}
                  </span>
                </div>
                {dim.assessment ? (
                  <p className="text-xs text-muted-foreground">{dim.assessment}</p>
                ) : null}
                {dim.suggested_action ? (
                  <p className="mt-2 text-xs text-foreground">
                    <span className="font-medium">Action: </span>
                    {dim.suggested_action}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ul>
      </section>

      <section data-testid="script-quality-priority-issues">
        <h2 className="mb-3 text-sm font-semibold text-foreground">
          Priority issues
        </h2>
        {review.priority_issues.length === 0 ? (
          <p className="text-sm text-muted-foreground">No priority issues.</p>
        ) : (
          <ul className="space-y-3">
            {review.priority_issues.map((issue) => {
              const applied = isIssueApplied(generation, issue.id);
              const canApply =
                Boolean(issue.original_excerpt && issue.suggested_rewrite) &&
                !staleInput &&
                !applied;
              return (
                <li
                  key={issue.id}
                  className="rounded-lg border border-border/60 bg-background/40 p-3"
                  data-testid={`script-quality-issue-${issue.id}`}
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={issue.severity} />
                    <span className="rounded-md border border-border px-1.5 py-0.5 text-[11px] capitalize text-muted-foreground">
                      {issue.category.replaceAll("_", " ")}
                    </span>
                    {issue.location_hint ? (
                      <span className="text-[11px] text-muted-foreground">
                        {issue.location_hint}
                      </span>
                    ) : null}
                    {applied ? (
                      <span className="rounded-md border border-success/30 bg-success/15 px-1.5 py-0.5 text-[11px] text-success">
                        Applied
                      </span>
                    ) : null}
                  </div>
                  {issue.problem ? (
                    <p className="text-sm text-foreground">{issue.problem}</p>
                  ) : null}
                  {issue.recommended_change ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {issue.recommended_change}
                    </p>
                  ) : null}
                  {issue.original_excerpt ? (
                    <div className="mt-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        Excerpt
                      </p>
                      <pre className="mt-1 whitespace-pre-wrap rounded-md border border-border bg-surface/60 p-2 text-xs text-foreground">
                        {issue.original_excerpt}
                      </pre>
                    </div>
                  ) : null}
                  {issue.suggested_rewrite ? (
                    <div className="mt-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        Suggested rewrite
                      </p>
                      <pre className="mt-1 whitespace-pre-wrap rounded-md border border-border bg-surface/60 p-2 text-xs text-foreground">
                        {issue.suggested_rewrite}
                      </pre>
                    </div>
                  ) : null}
                  <div className="mt-3 flex justify-end">
                    <Button
                      type="button"
                      variant="secondary"
                      className="h-8 text-xs"
                      disabled={!canApply || applySuggestion.isPending}
                      onClick={() => {
                        setApplyError(null);
                        setConfirmIssue(issue);
                      }}
                      data-testid={`script-quality-apply-${issue.id}`}
                    >
                      {applied
                        ? "Already applied"
                        : staleInput
                          ? "Blocked (stale)"
                          : "Apply suggestion"}
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section data-testid="script-quality-factual-risks">
        <h2 className="mb-3 text-sm font-semibold text-foreground">
          Factual risks
        </h2>
        {review.factual_risks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No factual risks flagged.</p>
        ) : (
          <ul className="space-y-3">
            {review.factual_risks.map((risk, index) => (
              <li
                key={`${risk.claim}-${index}`}
                className="rounded-lg border border-border/60 bg-background/40 p-3"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={risk.risk_level} />
                  <span className="rounded-md border border-warning/40 bg-warning/10 px-1.5 py-0.5 text-[11px] font-medium text-warning">
                    Human verification required
                  </span>
                </div>
                <p className="text-sm text-foreground">{risk.claim}</p>
                {risk.reason ? (
                  <p className="mt-1 text-xs text-muted-foreground">{risk.reason}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="grid gap-4 sm:grid-cols-2"
        data-testid="script-quality-promise-pacing"
      >
        <div className="rounded-lg border border-border/60 bg-background/40 p-3">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Viewer promise
          </h2>
          <p className="text-sm text-foreground">
            {review.promise_analysis.promise_made || "—"}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Delivered:{" "}
            {review.promise_analysis.promise_delivered ? "Yes" : "No"}
          </p>
          {review.promise_analysis.explanation ? (
            <p className="mt-1 text-xs text-muted-foreground">
              {review.promise_analysis.explanation}
            </p>
          ) : null}
        </div>

        <div className="rounded-lg border border-border/60 bg-background/40 p-3">
          <h2 className="mb-2 text-sm font-semibold text-foreground">Pacing</h2>
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-muted-foreground">Deterministic words</dt>
              <dd className="tabular-nums text-foreground">
                {metrics?.word_count ?? pacing.estimated_word_count}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Est. duration</dt>
              <dd className="tabular-nums text-foreground">
                {metrics?.estimated_duration_seconds ??
                  pacing.estimated_duration_seconds}
                s
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Target duration</dt>
              <dd className="tabular-nums text-foreground">
                {metrics?.target_duration_seconds ??
                  pacing.target_duration_seconds}
                s
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Status</dt>
              <dd className="text-foreground">
                {PACING_STATUS_LABELS[
                  metrics?.pacing_status ?? pacing.status
                ] ?? pacing.status}
              </dd>
            </div>
          </dl>
          {pacing.slow_sections.length > 0 ? (
            <div className="mt-3">
              <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Slow sections (AI)
              </p>
              <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                {pacing.slow_sections.map((item, i) => (
                  <li key={`slow-${i}`}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {pacing.rushed_sections.length > 0 ? (
            <div className="mt-3">
              <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Rushed sections (AI)
              </p>
              <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                {pacing.rushed_sections.map((item, i) => (
                  <li key={`rushed-${i}`}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </section>

      <Modal
        open={Boolean(confirmIssue)}
        onClose={() => {
          setConfirmIssue(null);
          setApplyError(null);
        }}
        title="Apply suggestion?"
        description="Replaces the original excerpt in the Master Script. This does not create a Content Version."
        size="md"
      >
        {confirmIssue ? (
          <div className="space-y-4" data-testid="script-quality-apply-confirm">
            {staleInput ? (
              <div
                className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
                role="alert"
              >
                This review is stale. Run a new quality review before applying
                suggestions.
              </div>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Replace the excerpt below with the suggested rewrite?
                </p>
                <pre className="max-h-32 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-surface/60 p-2 text-xs">
                  {confirmIssue.original_excerpt}
                </pre>
                <pre className="max-h-32 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-surface/60 p-2 text-xs">
                  {confirmIssue.suggested_rewrite}
                </pre>
              </>
            )}
            {applyError ? (
              <div
                className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
                role="alert"
              >
                {applyError}
              </div>
            ) : null}
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setConfirmIssue(null);
                  setApplyError(null);
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                loading={applySuggestion.isPending}
                disabled={staleInput || applySuggestion.isPending}
                onClick={() => void doApply(confirmIssue)}
                data-testid="script-quality-apply-confirm-submit"
              >
                Apply replace
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
