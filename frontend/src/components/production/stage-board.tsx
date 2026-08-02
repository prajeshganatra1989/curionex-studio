"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { QueueItemCard } from "@/components/production/queue-item-card";
import { EmptyState } from "@/components/ui/empty-state";
import {
  PRODUCTION_STAGES,
  productionStageLabel,
  type ProductionQueueItem,
  type ProductionStage,
} from "@/lib/production/types";
import { cn } from "@/lib/utils";

const BOARD_PREVIEW = 3;

/** Stages shown on the board (exclude archived by default). */
const BOARD_STAGES: ProductionStage[] = PRODUCTION_STAGES.filter(
  (stage) => stage !== "archived",
);

type StageBoardProps = {
  items: ProductionQueueItem[];
  stageCounts?: Record<string, number>;
  className?: string;
};

export function StageBoard({ items, stageCounts, className }: StageBoardProps) {
  const grouped = useMemo(() => {
    const map = new Map<ProductionStage, ProductionQueueItem[]>();
    for (const stage of BOARD_STAGES) {
      map.set(stage, []);
    }
    for (const item of items) {
      const list = map.get(item.production_stage);
      if (list) list.push(item);
      else map.set(item.production_stage, [item]);
    }
    return map;
  }, [items]);

  const hasAny = items.length > 0;

  if (!hasAny) {
    return (
      <EmptyState
        title="No items to board"
        description="Queue items will appear here grouped by production stage."
      />
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-4 lg:flex-row lg:items-start lg:gap-3 lg:overflow-x-auto lg:pb-2",
        className,
      )}
      data-testid="stage-board"
    >
      {BOARD_STAGES.map((stage) => {
        const stageItems = grouped.get(stage) ?? [];
        const count = stageCounts?.[stage] ?? stageItems.length;
        if (count === 0 && stageItems.length === 0) return null;
        return (
          <StageColumn
            key={stage}
            stage={stage}
            items={stageItems}
            count={count}
          />
        );
      })}
    </div>
  );
}

function StageColumn({
  stage,
  items,
  count,
}: {
  stage: ProductionStage;
  items: ProductionQueueItem[];
  count: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, BOARD_PREVIEW);
  const hiddenCount = Math.max(0, items.length - BOARD_PREVIEW);

  return (
    <section
      className="w-full shrink-0 rounded-xl border border-border/70 bg-surface/30 lg:w-72"
      data-testid={`stage-column-${stage}`}
    >
      <header className="flex items-center justify-between gap-2 border-b border-border px-3 py-2.5">
        <h3 className="text-xs font-semibold text-foreground">
          {productionStageLabel(stage)}
        </h3>
        <span className="rounded-md border border-border bg-surface px-1.5 py-0.5 text-[10px] tabular-nums text-muted-foreground">
          {count}
        </span>
      </header>
      <div className="space-y-2 p-2">
        {visible.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">
            No items in this page
          </p>
        ) : (
          visible.map((item) => (
            <QueueItemCard
              key={`${item.project_id}-${item.script_id ?? "p"}`}
              item={item}
              compact
            />
          ))
        )}
        {hiddenCount > 0 ? (
          <button
            type="button"
            className="flex w-full items-center justify-center gap-1 rounded-lg px-2 py-2 text-xs font-medium text-brand-orange hover:bg-surface-hover"
            onClick={() => setExpanded((value) => !value)}
            data-testid={`view-more-${stage}`}
          >
            {expanded ? (
              <>
                Show less <ChevronUp className="h-3.5 w-3.5" />
              </>
            ) : (
              <>
                View more ({hiddenCount}) <ChevronDown className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        ) : null}
      </div>
    </section>
  );
}
