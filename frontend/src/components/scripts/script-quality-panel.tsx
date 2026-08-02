"use client";

import Link from "next/link";
import { ClipboardCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { useLatestScriptQualityReview } from "@/lib/ai/hooks";
import {
  qualityReviewFromGeneration,
  qualityReviewHref,
  recommendationLabel,
} from "@/lib/scripts/quality";
import { formatRelativeTime } from "@/lib/utils";

type ScriptQualityPanelProps = {
  projectId: string;
  scriptId: string;
  /** True when Master Script has content (saved or draft). */
  hasMasterScript?: boolean;
  readOnly?: boolean;
  onReview: () => void;
};

export function ScriptQualityPanel({
  projectId,
  scriptId,
  hasMasterScript = true,
  readOnly,
  onReview,
}: ScriptQualityPanelProps) {
  const latestQuery = useLatestScriptQualityReview(scriptId);
  const generation = latestQuery.data ?? null;
  const review = qualityReviewFromGeneration(generation);

  return (
    <div
      className="rounded-xl border border-border/70 bg-surface/40 p-4"
      data-testid="script-quality-panel"
    >
      <div className="mb-3 flex items-center gap-2">
        <ClipboardCheck className="h-4 w-4 text-brand-orange" />
        <h3 className="text-sm font-semibold text-foreground">
          Script Quality
        </h3>
      </div>
      <p className="mb-3 text-xs text-muted-foreground">
        Advisory AI review of the Master Script. Never auto-applies and never
        creates a Content Version.
      </p>

      {latestQuery.isLoading ? (
        <LoadingSkeleton className="h-24" />
      ) : null}

      {!latestQuery.isLoading && !generation ? (
        <EmptyState
          className="px-3 py-6"
          title="No quality review yet"
          description="Run a review after the Master Script is ready."
        />
      ) : null}

      {!latestQuery.isLoading && generation && review ? (
        <div className="space-y-3" data-testid="script-quality-panel-summary">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Overall score
              </p>
              <p
                className="text-2xl font-semibold tabular-nums text-foreground"
                data-testid="script-quality-score"
              >
                {review.overall_score}
              </p>
            </div>
            <div className="text-right">
              <span
                className="inline-flex rounded-md border border-border bg-surface-hover px-2 py-0.5 text-xs font-medium text-foreground"
                data-testid="script-quality-band"
              >
                {review.quality_band_label}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span
              className="inline-flex rounded-md border border-info/30 bg-info/15 px-2 py-0.5 text-xs font-medium text-info"
              data-testid="script-quality-recommendation"
            >
              {recommendationLabel(review.recommended_next_action)}
            </span>
            {generation.stale_input ? (
              <span
                className="inline-flex rounded-md border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs font-medium text-warning"
                data-testid="script-quality-stale"
              >
                Stale input
              </span>
            ) : null}
          </div>

          <p className="text-[11px] text-muted-foreground">
            Reviewed{" "}
            <time dateTime={generation.created_at}>
              {formatRelativeTime(generation.created_at)}
            </time>
          </p>

          <p className="line-clamp-3 text-xs text-muted-foreground">
            {review.summary || "No summary provided."}
          </p>
        </div>
      ) : null}

      {!latestQuery.isLoading && generation && !review ? (
        <p className="text-xs text-muted-foreground">
          Latest review is missing structured output.
        </p>
      ) : null}

      <div className="mt-3 space-y-2 border-t border-border/60 pt-3">
        {!readOnly ? (
          <Button
            type="button"
            className="w-full"
            disabled={!hasMasterScript}
            onClick={onReview}
            data-testid="script-quality-panel-review"
          >
            Review Script Quality
          </Button>
        ) : null}
        {generation ? (
          <Link
            href={qualityReviewHref(projectId, scriptId, generation.id)}
            className="inline-flex h-10 w-full items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
            data-testid="script-quality-panel-open"
          >
            Open Full Review
          </Link>
        ) : null}
        {!hasMasterScript && !readOnly ? (
          <p className="text-[11px] text-muted-foreground">
            Write a Master Script before running a quality review.
          </p>
        ) : null}
      </div>
    </div>
  );
}
