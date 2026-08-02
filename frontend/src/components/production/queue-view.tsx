"use client";

import { QueueItemCard } from "@/components/production/queue-item-card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import type { ProductionQueueItem } from "@/lib/production/types";

type QueueViewProps = {
  items: ProductionQueueItem[];
  page: number;
  pageSize: number;
  total: number;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onPageChange: (page: number) => void;
  onRetry: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
};

export function QueueView({
  items,
  page,
  pageSize,
  total,
  isLoading,
  isError,
  errorMessage,
  onPageChange,
  onRetry,
  emptyTitle = "Nothing in the queue",
  emptyDescription = "Adjust filters or create a project to start production.",
  emptyAction,
}: QueueViewProps) {
  if (isLoading) {
    return (
      <div className="space-y-3" aria-busy="true" data-testid="queue-loading">
        {Array.from({ length: 4 }).map((_, index) => (
          <LoadingSkeleton key={index} className="h-28" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        message={errorMessage ?? "Unable to load production queue."}
        action={
          <button
            type="button"
            className="text-sm text-brand-orange underline"
            onClick={onRetry}
          >
            Try again
          </button>
        }
      />
    );
  }

  if (items.length === 0) {
    return (
      <div data-testid="queue-empty">
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          action={emptyAction}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="queue-view">
      <ul className="space-y-3">
        {items.map((item) => (
          <li
            key={`${item.project_id}-${item.script_id ?? "project"}-${item.production_stage}`}
          >
            <QueueItemCard item={item} />
          </li>
        ))}
      </ul>
      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={onPageChange}
      />
    </div>
  );
}
