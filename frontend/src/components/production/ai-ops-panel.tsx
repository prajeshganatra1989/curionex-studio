"use client";

import Link from "next/link";
import { AlertCircle, Sparkles } from "lucide-react";

import { SectionPanel } from "@/components/ui/section-panel";
import type { ProductionAiSummary } from "@/lib/production/types";
import { cn } from "@/lib/utils";

type AiOpsPanelProps = {
  ai: ProductionAiSummary | undefined;
  isLoading?: boolean;
  className?: string;
};

export function AiOpsPanel({ ai, isLoading, className }: AiOpsPanelProps) {
  return (
    <SectionPanel
      title="AI Ops"
      description="Live job health — AI never marks scripts Approved."
      action={
        <Link
          href="/ai/jobs"
          className="text-xs font-medium text-brand-orange hover:underline"
        >
          Jobs
        </Link>
      }
      className={className}
    >
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4" data-testid="ai-ops-panel">
        <Stat label="Queued" value={ai?.queued} loading={isLoading} />
        <Stat
          label="Running"
          value={ai?.running}
          loading={isLoading}
          accent={ai && ai.running > 0 ? "warning" : undefined}
        />
        <Stat
          label="Failed"
          value={ai?.failed}
          loading={isLoading}
          accent={ai && ai.failed > 0 ? "danger" : undefined}
        />
        <Stat
          label="Done today"
          value={ai?.completed_today}
          loading={isLoading}
        />
      </div>
      <div className="mt-3 space-y-1 border-t border-border/60 pt-3 text-xs text-muted-foreground">
        <p className="inline-flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5" aria-hidden />
          Est. cost today:{" "}
          {ai == null ? "—" : `$${ai.estimated_cost_today.toFixed(2)}`}
        </p>
        <p>
          Est. cost this week:{" "}
          {ai == null ? "—" : `$${ai.estimated_cost_this_week.toFixed(2)}`}
        </p>
        {ai && ai.failed > 0 ? (
          <p className="inline-flex items-center gap-1.5 text-danger">
            <AlertCircle className="h-3.5 w-3.5" aria-hidden />
            Failed jobs need attention in the job monitor.
          </p>
        ) : null}
      </div>
    </SectionPanel>
  );
}

function Stat({
  label,
  value,
  loading,
  accent,
}: {
  label: string;
  value: number | undefined;
  loading?: boolean;
  accent?: "warning" | "danger";
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border/60 bg-surface/40 px-3 py-2",
        accent === "warning" && "border-warning/30 bg-warning/5",
        accent === "danger" && "border-danger/30 bg-danger/5",
      )}
    >
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p
        className={cn(
          "mt-1 text-lg font-semibold tabular-nums text-foreground",
          accent === "warning" && "text-warning",
          accent === "danger" && "text-danger",
        )}
      >
        {loading ? "…" : value == null ? "—" : value}
      </p>
    </div>
  );
}
