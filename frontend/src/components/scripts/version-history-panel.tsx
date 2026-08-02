"use client";

import Link from "next/link";
import { memo, useMemo } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type {
  WorkflowApprovalSummary,
  WorkflowStatus,
} from "@/lib/api/types";
import { useScriptVersions } from "@/lib/scripts/hooks";
import { formatRelativeTime } from "@/lib/utils";

type VersionHistoryPanelProps = {
  projectId: string;
  scriptId: string;
  workflow?: WorkflowStatus;
  latestApproval?: WorkflowApprovalSummary | null;
};

function approvalIdForVersion(
  versionId: string,
  workflow?: WorkflowStatus,
  latestApproval?: WorkflowApprovalSummary | null,
): string | null {
  if (workflow?.pending_approval?.content_version_id === versionId) {
    return workflow.pending_approval.id;
  }
  if (latestApproval?.content_version_id === versionId) {
    return latestApproval.id;
  }
  return null;
}

export const VersionHistoryPanel = memo(function VersionHistoryPanel({
  projectId,
  scriptId,
  workflow,
  latestApproval,
}: VersionHistoryPanelProps) {
  const versionsQuery = useScriptVersions(scriptId);

  const items = useMemo(
    () => versionsQuery.data?.items ?? [],
    [versionsQuery.data?.items],
  );

  const roleMap = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const version of items) {
      const roles: string[] = [];
      if (workflow?.latest_version?.id === version.id) roles.push("Latest");
      if (workflow?.active_version?.id === version.id) roles.push("Active");
      if (workflow?.approved_version?.id === version.id) roles.push("Approved");
      map.set(version.id, roles);
    }
    return map;
  }, [items, workflow]);

  return (
    <aside
      className="space-y-3 rounded-xl border border-border/70 bg-surface/60 p-4"
      data-testid="version-history-panel"
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        Version history
      </p>

      {versionsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading versions…</p>
      ) : null}

      {!versionsQuery.isLoading && items.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No versions yet. Create a version when the workspace is ready.
        </p>
      ) : null}

      <ul className="space-y-2">
        {items.map((version) => {
          const roles = roleMap.get(version.id) ?? [];
          const approvalId = approvalIdForVersion(
            version.id,
            workflow,
            latestApproval,
          );
          const versionHref = `/projects/${projectId}/scripts/${scriptId}/versions/${version.id}`;
          return (
            <li
              key={version.id}
              className="rounded-lg border border-border/60 px-3 py-2"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm text-foreground">
                  v{version.version_number}
                </span>
                <StatusBadge status={version.status} />
                {roles.map((role) => (
                  <span
                    key={role}
                    className="rounded-md border border-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground"
                  >
                    {role}
                  </span>
                ))}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatRelativeTime(version.created_at)}
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                <Link
                  href={versionHref}
                  className="inline-flex h-8 items-center rounded-lg px-2 text-sm text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                >
                  Open Version
                </Link>
                {approvalId ? (
                  <Link
                    href={`/reviews/${approvalId}`}
                    className="inline-flex h-8 items-center rounded-lg px-2 text-sm text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                  >
                    Open Review
                  </Link>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
});
