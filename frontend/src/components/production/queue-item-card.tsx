"use client";

import Link from "next/link";
import {
  AlertTriangle,
  Clock,
  FileText,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import type { ProductionQueueItem } from "@/lib/production/types";
import { productionStageLabel } from "@/lib/production/types";
import { formatRelativeTime, cn } from "@/lib/utils";

type QueueItemCardProps = {
  item: ProductionQueueItem;
  compact?: boolean;
};

export function QueueItemCard({ item, compact = false }: QueueItemCardProps) {
  const title =
    item.script_title?.trim() ||
    item.script_code ||
    item.project_name;
  const qualityScore = item.quality.score;
  const aiStatus = item.ai_job.status;

  return (
    <article
      className={cn(
        "rounded-xl border border-border/70 bg-surface/40 p-4 transition hover:border-border-strong hover:bg-surface-hover/40",
        compact && "p-3",
      )}
      data-testid="queue-item-card"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-medium text-foreground">
              {title}
            </h3>
            <StatusBadge status={item.production_stage} />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.project_code}
            {item.script_code ? (
              <>
                <span aria-hidden> · </span>
                {item.script_code}
              </>
            ) : null}
            <span aria-hidden> · </span>
            <time dateTime={item.updated_at}>
              {formatRelativeTime(item.updated_at)}
            </time>
          </p>

          {!compact ? (
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" aria-hidden />
                KP {item.knowledge_pack_completion}%
              </span>
              {qualityScore != null ? (
                <span
                  className={cn(
                    "inline-flex items-center gap-1",
                    item.quality.stale && "text-warning",
                  )}
                  title="Quality score is advisory — not approval"
                >
                  Quality {qualityScore}
                  {item.quality.stale ? " (stale)" : ""}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-muted-foreground/80">
                  No quality score
                </span>
              )}
              {aiStatus ? (
                <span className="inline-flex items-center gap-1">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden />
                  AI {aiStatus}
                </span>
              ) : null}
              {item.quality.high_risk_facts > 0 ? (
                <span className="inline-flex items-center gap-1 text-danger">
                  <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
                  {item.quality.high_risk_facts} fact flag
                  {item.quality.high_risk_facts === 1 ? "" : "s"}
                </span>
              ) : null}
            </div>
          ) : null}

          <p className="mt-2 text-xs text-muted-foreground">
            <Clock className="mr-1 inline h-3.5 w-3.5" aria-hidden />
            {item.next_action.reason ||
              `Next: ${productionStageLabel(item.production_stage)}`}
          </p>
        </div>

        <div className="shrink-0">
          {item.next_action.href ? (
            <Link
              href={item.next_action.href}
              data-testid="next-action"
              className={cn(
                "inline-flex h-9 items-center justify-center rounded-lg px-3 text-sm transition",
                item.next_action.blocked
                  ? "border border-border bg-surface-elevated text-foreground hover:bg-surface-hover"
                  : "bg-brand-gradient font-semibold text-black shadow-[var(--glow-brand)] hover:brightness-110",
              )}
            >
              {item.next_action.label}
            </Link>
          ) : (
            <Button
              type="button"
              variant="secondary"
              className="h-9 px-3"
              disabled
              data-testid="next-action"
            >
              {item.next_action.label}
            </Button>
          )}
        </div>
      </div>
    </article>
  );
}
