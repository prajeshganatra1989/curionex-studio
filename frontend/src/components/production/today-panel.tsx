"use client";

import Link from "next/link";

import { SectionPanel } from "@/components/ui/section-panel";
import type {
  ProductionGoalsSummary,
  ProductionMetrics,
} from "@/lib/production/types";
import { cn } from "@/lib/utils";

type TodayPanelProps = {
  goals: ProductionGoalsSummary | undefined;
  metrics: ProductionMetrics | undefined;
  isLoading?: boolean;
  className?: string;
};

export function TodayPanel({
  goals,
  metrics,
  isLoading,
  className,
}: TodayPanelProps) {
  return (
    <SectionPanel
      title="Today"
      description="Pace against daily and weekly targets."
      action={
        <Link
          href="/reviews?status=pending"
          className="text-xs font-medium text-brand-orange hover:underline"
        >
          Reviews
        </Link>
      }
      className={className}
    >
      <div className="space-y-3" data-testid="today-panel">
        <Row
          label="Approved today"
          value={
            goals
              ? `${goals.approved_today} / ${goals.daily_target}`
              : undefined
          }
          loading={isLoading}
        />
        <Row
          label="Approved this week"
          value={
            goals
              ? `${goals.approved_this_week} / ${goals.weekly_target}`
              : undefined
          }
          loading={isLoading}
        />
        <Row
          label="Versions created (range)"
          value={metrics?.versions_created}
          loading={isLoading}
        />
        <Row
          label="Avg days to approval"
          value={
            metrics?.average_days_to_approval == null
              ? null
              : metrics.average_days_to_approval.toFixed(1)
          }
          loading={isLoading}
        />
      </div>
    </SectionPanel>
  );
}

function Row({
  label,
  value,
  loading,
}: {
  label: string;
  value: string | number | null | undefined;
  loading?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          "tabular-nums font-medium text-foreground",
          (value === null || value === undefined) && !loading && "text-muted-foreground",
        )}
      >
        {loading ? "…" : value == null ? "—" : value}
      </span>
    </div>
  );
}
