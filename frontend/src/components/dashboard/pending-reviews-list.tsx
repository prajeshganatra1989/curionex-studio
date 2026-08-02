import Link from "next/link";

import { StatusBadge } from "@/components/ui/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { PendingReview } from "@/lib/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";

type PendingReviewsListProps = {
  reviews: PendingReview[];
  restricted?: boolean;
};

export function PendingReviewsList({
  reviews,
  restricted = false,
}: PendingReviewsListProps) {
  if (restricted) {
    return (
      <EmptyState
        title="Access restricted"
        description="You do not have permission to view pending approvals."
      />
    );
  }

  if (reviews.length === 0) {
    return (
      <EmptyState
        title="No pending reviews"
        description="Approvals waiting for review will show up here."
      />
    );
  }

  return (
    <ul className="divide-y divide-border">
      {reviews.map((review) => (
        <li key={review.id}>
          <Link
            href={`/reviews/${review.id}`}
            className="flex items-center gap-3 rounded-md px-2 py-3 hover:bg-surface-hover"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface-elevated text-[11px] font-semibold text-foreground">
              {review.reviewerInitials ?? "—"}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate text-sm font-medium">{review.title}</p>
                <StatusBadge status={review.status} />
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {review.projectCode ? `${review.projectCode} · ` : null}
                v{review.versionNumber}
                <span aria-hidden> · </span>
                <time dateTime={review.updatedAt}>
                  {formatRelativeTime(review.updatedAt)}
                </time>
              </p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
