"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { SectionPanel } from "@/components/ui/section-panel";
import type { ProductionActivityItem } from "@/lib/production/types";
import { formatRelativeTime } from "@/lib/utils";

type RecentActivityProps = {
  items: ProductionActivityItem[];
  restricted?: boolean;
  isLoading?: boolean;
  className?: string;
};

export function RecentActivity({
  items,
  restricted = false,
  isLoading,
  className,
}: RecentActivityProps) {
  return (
    <SectionPanel
      title="Recent activity"
      description="Production-related audit events."
      className={className}
    >
      <div data-testid="recent-activity">
        {isLoading ? (
          <div className="space-y-2" aria-busy="true">
            {Array.from({ length: 4 }).map((_, index) => (
              <LoadingSkeleton key={index} className="h-12" />
            ))}
          </div>
        ) : null}

        {!isLoading && restricted ? (
          <EmptyState
            title="Activity restricted"
            description="You need audit access to view production activity."
          />
        ) : null}

        {!isLoading && !restricted && items.length === 0 ? (
          <EmptyState
            title="No recent activity"
            description="Approvals, versions, and AI jobs will show up here."
          />
        ) : null}

        {!isLoading && !restricted && items.length > 0 ? (
          <ol className="space-y-2">
            {items.map((item) => (
              <li
                key={item.id}
                className="rounded-lg border border-border/50 px-3 py-2"
              >
                <p className="text-sm text-foreground">{item.action_label}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  <time dateTime={item.created_at}>
                    {formatRelativeTime(item.created_at)}
                  </time>
                  <span aria-hidden> · </span>
                  {item.entity_type}
                </p>
              </li>
            ))}
          </ol>
        ) : null}
      </div>
    </SectionPanel>
  );
}
