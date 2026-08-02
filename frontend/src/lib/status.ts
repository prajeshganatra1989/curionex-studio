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
  ready: "Ready",
  versioning: "Versioning",
  review: "Review",
  workspace: "Workspace",
  queued: "Queued",
  running: "Running",
  cancelled: "Cancelled",
  failed: "Failed",
  idea: "Idea",
  research: "Research",
  discovery_brief: "Discovery Brief",
  story_spine: "Story Spine",
  master_script: "Master Script",
  quality_review: "Quality Review",
  needs_revision: "Needs Revision",
  ready_for_version: "Ready for Version",
  version_created: "Version Created",
  pending_human_review: "Pending Human Review",
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
    case "ready_for_version":
      return "success";
    case "in_review":
    case "pending":
    case "review":
    case "versioning":
    case "queued":
    case "running":
    case "pending_human_review":
    case "quality_review":
    case "version_created":
      return "warning";
    case "rejected":
    case "blocked":
    case "failed":
    case "needs_revision":
      return "danger";
    case "cancelled":
    case "archived":
      return "muted";
    case "draft":
    case "info":
    case "ready":
    case "idea":
    case "research":
    case "discovery_brief":
    case "story_spine":
    case "master_script":
      return "info";
    default:
      return "neutral";
  }
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll("_", " ");
}
