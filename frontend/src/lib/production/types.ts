export const PRODUCTION_STAGES = [
  "idea",
  "research",
  "discovery_brief",
  "story_spine",
  "master_script",
  "quality_review",
  "needs_revision",
  "ready_for_version",
  "version_created",
  "pending_human_review",
  "approved",
  "blocked",
  "archived",
] as const;

export type ProductionStage = (typeof PRODUCTION_STAGES)[number];

export const PRODUCTION_STAGE_LABELS: Record<ProductionStage, string> = {
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
  approved: "Approved",
  blocked: "Blocked",
  archived: "Archived",
};

export const QUALITY_BANDS = [
  "excellent",
  "strong",
  "needs_refinement",
  "weak",
  "major_revision_required",
] as const;

export type QualityBand = (typeof QUALITY_BANDS)[number];

export const QUALITY_BAND_LABELS: Record<QualityBand, string> = {
  excellent: "Excellent",
  strong: "Strong",
  needs_refinement: "Needs refinement",
  weak: "Weak",
  major_revision_required: "Major revision required",
};

export const MILESTONE_THRESHOLDS = [10, 25, 50, 75, 100, 120] as const;

export type MetricsRange = "today" | "7d" | "30d";

export type DocumentStatus = "complete" | "incomplete" | "missing";

export type ProductionNextAction = {
  code: string;
  label: string;
  href: string | null;
  reason: string;
  blocked: boolean;
};

export type ProductionGoalsSummary = {
  approved_target: number;
  approved_total: number;
  remaining: number;
  completion_percent: number;
  daily_target: number;
  approved_today: number;
  weekly_target: number;
  approved_this_week: number;
  projected_days_remaining: number | null;
};

export type ProductionAiSummary = {
  queued: number;
  running: number;
  failed: number;
  completed_today: number;
  estimated_cost_today: number;
  estimated_cost_this_week: number;
};

export type ProductionQualitySummary = {
  average_current_score: number | null;
  scripts_needing_revision: number;
  stale_reviews: number;
  high_risk_fact_flags: number;
};

export type ProductionCatalogSummary = {
  projects: number;
  knowledge_packs: number;
  scripts: number;
  draft_scripts: number;
};

export type ProductionOverview = {
  goals: ProductionGoalsSummary;
  stage_counts: Record<string, number>;
  ai: ProductionAiSummary;
  quality: ProductionQualitySummary;
  catalog: ProductionCatalogSummary;
};

export type ProductionDocumentStatuses = {
  discovery_brief: DocumentStatus;
  story_spine: DocumentStatus;
  master_script: DocumentStatus;
};

export type ProductionQualityItem = {
  score: number | null;
  band: string | null;
  stale: boolean;
  recommendation: string | null;
  generation_id: string | null;
  high_risk_facts: number;
};

export type ProductionWorkflowItem = {
  stage: string | null;
  status: string | null;
  active_version_id: string | null;
};

export type ProductionApprovalItem = {
  status: string | null;
  approval_id: string | null;
};

export type ProductionAiJobItem = {
  status: string | null;
  job_id: string | null;
  purpose: string | null;
  error_message: string | null;
};

export type ProductionQueueItem = {
  script_id: string | null;
  project_id: string;
  project_code: string;
  project_name: string;
  script_code: string | null;
  script_title: string | null;
  script_status: string | null;
  production_stage: ProductionStage;
  next_action: ProductionNextAction;
  knowledge_pack_id: string | null;
  knowledge_pack_completion: number;
  documents: ProductionDocumentStatuses;
  quality: ProductionQualityItem;
  workflow: ProductionWorkflowItem;
  approval: ProductionApprovalItem;
  ai_job: ProductionAiJobItem;
  updated_at: string;
};

export type ProductionQueueResponse = {
  items: ProductionQueueItem[];
  page: number;
  page_size: number;
  total: number;
};

export type ProductionQueueParams = {
  page?: number;
  page_size?: number;
  production_stage?: string;
  project_id?: string;
  category_id?: string;
  tag_id?: string;
  search?: string;
  quality_band?: string;
  ai_job_status?: string;
  stale_quality?: boolean;
  blocked_only?: boolean;
  pending_approval?: boolean;
  script_status?: string;
  sort?: string;
};

export type ProductionMetrics = {
  range: MetricsRange;
  scripts_approved: number;
  versions_created: number;
  quality_reviews_completed: number;
  average_quality_score: number | null;
  ai_jobs_completed: number;
  ai_jobs_failed: number;
  estimated_ai_cost: number;
  average_days_to_approval: number | null;
};

export type ProductionActivityItem = {
  id: string;
  action: string;
  action_label: string;
  entity_type: string;
  entity_id: string | null;
  actor_user_id: string | null;
  created_at: string;
  metadata: Record<string, unknown> | null;
};

export type ProductionActivityResponse = {
  items: ProductionActivityItem[];
  restricted: boolean;
};

export type ProductionSettings = {
  id: string;
  approved_script_target: number;
  daily_approved_script_target: number;
  weekly_approved_script_target: number;
  updated_at: string;
  updated_by: string | null;
};

export type ProductionSettingsUpdate = {
  approved_script_target?: number;
  daily_approved_script_target?: number;
  weekly_approved_script_target?: number;
};

export type ProductionViewMode = "queue" | "board";

export type ProductionSessionTimelineStep = {
  key: string;
  label: string;
  status: "complete" | "current" | "upcoming";
};

export type ProductionSessionSidebar = {
  wave: number | null;
  priority: string | null;
  estimated_remaining_minutes: number;
  quality_score: number | null;
  quality_band: string | null;
  approval_status: string | null;
  knowledge_pack_status: string;
  knowledge_pack_completion: number;
  version_status: string | null;
  reviewer: string | null;
};

export type ProductionSessionCurrent = {
  topic_title: string;
  topic_id: string | null;
  topic_slug: string | null;
  project_id: string;
  project_code: string;
  project_name: string;
  script_id: string | null;
  script_title: string | null;
  production_stage: ProductionStage | string;
  stage_label: string;
  next_action: ProductionNextAction;
  continue_url: string | null;
  wave: number | null;
  priority: string | null;
  estimated_remaining_steps: number;
  timeline: ProductionSessionTimelineStep[];
  sidebar: ProductionSessionSidebar | null;
};

export type ProductionSessionQueueItem = Omit<
  ProductionSessionCurrent,
  "sidebar"
>;

export type ProductionSession = {
  today: {
    goal: number;
    completed: number;
    estimated_finish: string | null;
    current_streak: number;
  };
  progress: {
    approved_total: number;
    approved_target: number;
    remaining: number;
    completion_percent: number;
    approved_today: number;
  };
  current: ProductionSessionCurrent | null;
  upcoming: ProductionSessionQueueItem[];
  previous_completed: {
    topic_title: string;
    stage_label: string;
    project_id: string;
    script_id: string | null;
  } | null;
  warnings: string[];
  empty: boolean;
  browse_topics_url: string;
  settings: {
    daily_approved_script_target: number;
    approved_script_target: number;
  };
};

export function productionStageLabel(stage: string): string {
  if (stage in PRODUCTION_STAGE_LABELS) {
    return PRODUCTION_STAGE_LABELS[stage as ProductionStage];
  }
  return stage.replaceAll("_", " ");
}

export function achievedMilestones(approvedTotal: number): number[] {
  return MILESTONE_THRESHOLDS.filter((n) => approvedTotal >= n);
}
