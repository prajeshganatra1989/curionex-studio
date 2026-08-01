"use client";

import { memo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { StatusBadge } from "@/components/ui/status-badge";
import type { ContentVersionSummary, WorkflowStatus } from "@/lib/api/types";
import { useContentVersion, useScriptVersions } from "@/lib/scripts/hooks";
import { formatRelativeTime } from "@/lib/utils";

type VersionHistoryPanelProps = {
  projectId: string;
  scriptCode: string;
  workflow?: WorkflowStatus;
};

export const VersionHistoryPanel = memo(function VersionHistoryPanel({
  projectId,
  scriptCode,
  workflow,
}: VersionHistoryPanelProps) {
  const versionsQuery = useScriptVersions(projectId, scriptCode);
  const [openId, setOpenId] = useState<string | null>(null);
  const detailQuery = useContentVersion(openId);

  const items = versionsQuery.data?.items ?? [];

  function roleFor(version: ContentVersionSummary): string[] {
    const roles: string[] = [];
    if (workflow?.latest_version?.id === version.id) roles.push("Latest");
    if (workflow?.active_version?.id === version.id) roles.push("Active");
    if (workflow?.approved_version?.id === version.id) roles.push("Approved");
    return roles;
  }

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
          const roles = roleFor(version);
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
              <Button
                type="button"
                variant="ghost"
                className="mt-1 h-8 px-2"
                onClick={() => setOpenId(version.id)}
              >
                Open Version
              </Button>
            </li>
          );
        })}
      </ul>

      <Modal
        open={Boolean(openId)}
        onClose={() => setOpenId(null)}
        title={
          detailQuery.data
            ? `Version ${detailQuery.data.version_number}`
            : "Version"
        }
        description="Content versions are immutable snapshots."
        size="lg"
      >
        {detailQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : null}
        {detailQuery.data ? (
          <pre className="max-h-[50vh] overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-xs text-muted-foreground">
            {detailQuery.data.content}
          </pre>
        ) : null}
      </Modal>
    </aside>
  );
});
