"use client";

import Link from "next/link";

import { StatusBadge } from "@/components/ui/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { RecentScript } from "@/lib/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";

type RecentScriptsListProps = {
  scripts: RecentScript[];
  restricted?: boolean;
  unavailable?: boolean;
};

export function RecentScriptsList({
  scripts,
  restricted = false,
  unavailable = false,
}: RecentScriptsListProps) {
  if (restricted) {
    return (
      <EmptyState
        title="Scripts restricted"
        description="You need production.view to see recent scripts."
      />
    );
  }

  if (unavailable) {
    return (
      <EmptyState
        title="Temporarily unavailable"
        description="Could not load recent scripts. Try Refresh."
      />
    );
  }

  if (scripts.length === 0) {
    return (
      <EmptyState
        title="No scripts yet"
        description="Scripts from your projects will appear here."
      />
    );
  }

  return (
    <ul className="divide-y divide-border">
      {scripts.map((script) => (
        <li key={script.id}>
          <Link
            href={`/projects/${script.projectId}/scripts/${script.id}`}
            className="flex items-center gap-3 rounded-md px-2 py-3 transition hover:bg-surface-hover"
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate text-sm font-medium text-foreground">
                  {script.title}
                </p>
                <StatusBadge status={script.status} />
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                <span className="font-mono text-[11px] text-brand-amber">
                  {script.projectCode}
                </span>
                <span aria-hidden> · </span>
                <time dateTime={script.updatedAt}>
                  {formatRelativeTime(script.updatedAt)}
                </time>
              </p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
