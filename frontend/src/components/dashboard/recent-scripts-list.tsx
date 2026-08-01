"use client";

import { MoreHorizontal } from "lucide-react";

import { StatusBadge } from "@/components/ui/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { RecentScript } from "@/lib/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";

type RecentScriptsListProps = {
  scripts: RecentScript[];
};

export function RecentScriptsList({ scripts }: RecentScriptsListProps) {
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
        <li
          key={script.id}
          className="flex items-center gap-3 rounded-md px-2 py-3 hover:bg-surface-hover"
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
          <button
            type="button"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-surface-elevated hover:text-foreground"
            aria-label={`More actions for ${script.title}`}
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
