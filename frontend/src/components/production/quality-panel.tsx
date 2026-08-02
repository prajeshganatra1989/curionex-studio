"use client";

import { SectionPanel } from "@/components/ui/section-panel";
import type { ProductionQualitySummary } from "@/lib/production/types";
import { cn } from "@/lib/utils";

type QualityPanelProps = {
  quality: ProductionQualitySummary | undefined;
  isLoading?: boolean;
  className?: string;
};

export function QualityPanel({
  quality,
  isLoading,
  className,
}: QualityPanelProps) {
  return (
    <SectionPanel
      title="Quality"
      description="Advisory scores only — human approval is separate."
      className={className}
    >
      <div className="space-y-3" data-testid="quality-panel">
        <div className="rounded-lg border border-border/60 bg-surface/40 px-3 py-3">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Average score
          </p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
            {isLoading
              ? "…"
              : quality?.average_current_score == null
                ? "—"
                : Math.round(quality.average_current_score)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Not a substitute for Approved status
          </p>
        </div>
        <dl className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <Metric
            label="Needs revision"
            value={quality?.scripts_needing_revision}
            loading={isLoading}
            tone="warning"
          />
          <Metric
            label="Stale reviews"
            value={quality?.stale_reviews}
            loading={isLoading}
          />
          <Metric
            label="High-risk facts"
            value={quality?.high_risk_fact_flags}
            loading={isLoading}
            tone={
              quality && quality.high_risk_fact_flags > 0 ? "danger" : undefined
            }
          />
        </dl>
      </div>
    </SectionPanel>
  );
}

function Metric({
  label,
  value,
  loading,
  tone,
}: {
  label: string;
  value: number | undefined;
  loading?: boolean;
  tone?: "warning" | "danger";
}) {
  return (
    <div className="rounded-lg border border-border/60 px-3 py-2">
      <dt className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd
        className={cn(
          "mt-1 text-lg font-semibold tabular-nums text-foreground",
          tone === "warning" && "text-warning",
          tone === "danger" && "text-danger",
        )}
      >
        {loading ? "…" : value == null ? "—" : value}
      </dd>
    </div>
  );
}
