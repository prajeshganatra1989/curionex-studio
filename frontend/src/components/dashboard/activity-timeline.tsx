import { EmptyState } from "@/components/ui/empty-state";
import type { RecentActivity } from "@/lib/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";

type ActivityTimelineProps = {
  items: RecentActivity[];
  restricted?: boolean;
};

export function ActivityTimeline({
  items,
  restricted = false,
}: ActivityTimelineProps) {
  if (restricted) {
    return (
      <EmptyState
        title="Activity restricted"
        description="You need the audit.view permission to see recent activity."
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="No recent activity"
        description="Updates across scripts, versions, and packs will appear here."
      />
    );
  }

  return (
    <ol className="space-y-1">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex gap-3 rounded-md px-2 py-2.5 hover:bg-surface-hover"
        >
          <span
            aria-hidden
            className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-orange"
          />
          <div className="min-w-0 flex-1">
            <p className="text-sm text-foreground">{item.summary}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {item.actorName}
              <span aria-hidden> · </span>
              <time dateTime={item.createdAt}>
                {formatRelativeTime(item.createdAt)}
              </time>
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
