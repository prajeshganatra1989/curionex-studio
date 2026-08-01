"use client";

import { Button } from "@/components/ui/button";
import type { WorkflowApprovalSummary, WorkflowStatus } from "@/lib/api/types";

export type WorkflowActionKind =
  | "continue_writing"
  | "create_version"
  | "submit_review"
  | "view_review"
  | "approved"
  | "revisions_requested"
  | null;

export function resolveWorkflowAction(
  workflow: WorkflowStatus | undefined,
  docsComplete: boolean,
  latestApproval?: WorkflowApprovalSummary | null,
): { kind: WorkflowActionKind; label: string } {
  if (!workflow) return { kind: null, label: "" };

  const stage = workflow.stage;
  const revisionsRequested =
    stage === "workspace" &&
    (latestApproval?.status === "rejected" ||
      workflow.pending_approval?.status === "rejected");

  if (stage === "completed" || workflow.status === "completed") {
    return { kind: "approved", label: "Approved" };
  }

  if (stage === "review") {
    return { kind: "view_review", label: "View Review" };
  }

  if (stage === "versioning") {
    return { kind: "submit_review", label: "Submit for Review" };
  }

  if (stage === "workspace") {
    if (revisionsRequested) {
      return { kind: "revisions_requested", label: "Revisions Requested" };
    }
    if (!docsComplete) {
      return { kind: "continue_writing", label: "Continue Writing" };
    }
    return { kind: "create_version", label: "Create Version" };
  }

  return { kind: null, label: "" };
}

type WorkflowActionButtonProps = {
  kind: WorkflowActionKind;
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onAction: (kind: WorkflowActionKind) => void;
};

export function WorkflowActionButton({
  kind,
  label,
  loading,
  disabled,
  onAction,
}: WorkflowActionButtonProps) {
  if (!kind || !label) return null;

  const isDisplayOnly = kind === "approved";

  return (
    <Button
      type="button"
      variant={
        kind === "submit_review" || kind === "create_version"
          ? "primary"
          : "secondary"
      }
      loading={loading}
      disabled={disabled || isDisplayOnly}
      onClick={() => {
        if (!isDisplayOnly) onAction(kind);
      }}
      aria-label={label}
      data-testid="workflow-action"
      data-action={kind}
    >
      {label}
    </Button>
  );
}
