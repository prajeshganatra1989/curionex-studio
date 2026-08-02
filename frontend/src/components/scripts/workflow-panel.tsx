"use client";

import { memo } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type { WorkflowApprovalSummary, WorkflowStatus } from "@/lib/api/types";

type WorkflowPanelProps = {
  workflow: WorkflowStatus | undefined;
  latestApproval?: WorkflowApprovalSummary | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
};

function VersionRow({
  label,
  version,
}: {
  label: string;
  version: { version_number: number; status: string; title: string } | null;
}) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right">
        {version ? (
          <>
            <span className="font-mono text-foreground">
              v{version.version_number}
            </span>
            <span className="mt-0.5 block text-xs text-muted-foreground">
              {version.status}
            </span>
          </>
        ) : (
          <span className="text-muted-foreground">None</span>
        )}
      </dd>
    </div>
  );
}

export const WorkflowPanel = memo(function WorkflowPanel({
  workflow,
  latestApproval,
  loading,
  error,
  onRetry,
}: WorkflowPanelProps) {
  if (loading) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="workflow-loading">
        Loading workflow…
      </p>
    );
  }

  if (error) {
    return (
      <div className="space-y-2 text-sm" data-testid="workflow-error">
        <p className="text-danger">{error}</p>
        {onRetry ? (
          <button
            type="button"
            className="text-brand-orange underline"
            onClick={onRetry}
          >
            Retry
          </button>
        ) : null}
      </div>
    );
  }

  if (!workflow) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="workflow-missing">
        Workflow unavailable for this script.
      </p>
    );
  }

  const rejected =
    workflow.stage === "workspace" &&
    (latestApproval?.status === "rejected" ||
      workflow.pending_approval?.status === "rejected");

  return (
    <aside
      className="space-y-4 rounded-xl border border-border/70 bg-surface/60 p-4"
      data-testid="workflow-panel"
    >
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Workflow
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <StatusBadge status={workflow.stage} />
          <StatusBadge status={workflow.status} />
        </div>
      </div>

      {rejected ? (
        <div
          className="rounded-lg border border-brand-amber/40 bg-brand-amber/10 px-3 py-2 text-sm text-foreground"
          data-testid="revisions-banner"
        >
          <p className="font-medium">Revisions requested</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Update Script Documents, then create a new version. Approval comments
            are not copied into documents.
          </p>
        </div>
      ) : null}

      {workflow.stage === "completed" ? (
        <div
          className="rounded-lg border border-success/40 bg-success/10 px-3 py-2 text-sm"
          data-testid="approved-banner"
        >
          <p className="font-medium text-success">Approved</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Approved snapshot stays immutable. Workspace edits do not change it
            until you create a new version.
          </p>
        </div>
      ) : null}

      {workflow.stage === "review" && workflow.pending_approval ? (
        <div
          className="rounded-lg border border-border px-3 py-2 text-sm"
          data-testid="pending-review-banner"
        >
          <p className="font-medium text-foreground">Pending review</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Approval {workflow.pending_approval.status}. Full review decisions
            arrive in the next sprint.
          </p>
        </div>
      ) : null}

      <dl className="space-y-3 border-t border-border/70 pt-4">
        <VersionRow label="Latest" version={workflow.latest_version} />
        <VersionRow label="Active" version={workflow.active_version} />
        <VersionRow label="Approved" version={workflow.approved_version} />
        <div className="flex items-start justify-between gap-3 text-sm">
          <dt className="text-muted-foreground">Pending approval</dt>
          <dd className="text-right text-foreground">
            {workflow.pending_approval
              ? workflow.pending_approval.status
              : "None"}
          </dd>
        </div>
      </dl>
    </aside>
  );
});
