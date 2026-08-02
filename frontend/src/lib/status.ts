export const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  active: "Active",
  in_progress: "In progress",
  in_review: "In review",
  approved: "Approved",
  rejected: "Rejected",
  archived: "Archived",
  completed: "Completed",
  pending: "Pending",
  blocked: "Blocked",
  versioning: "Versioning",
  review: "Review",
  workspace: "Workspace",
  queued: "Queued",
  running: "Running",
  cancelled: "Cancelled",
  failed: "Failed",
};

export type StatusTone =
  | "neutral"
  | "info"
  | "warning"
  | "success"
  | "danger"
  | "muted";

export function statusTone(status: string): StatusTone {
  switch (status) {
    case "approved":
    case "completed":
    case "active":
      return "success";
    case "in_review":
    case "pending":
    case "review":
    case "versioning":
    case "queued":
    case "running":
      return "warning";
    case "rejected":
    case "blocked":
    case "failed":
      return "danger";
    case "cancelled":
      return "muted";
    case "draft":
    case "info":
      return "info";
    case "archived":
      return "muted";
    default:
      return "neutral";
  }
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll("_", " ");
}
