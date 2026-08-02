import { ApiError, type ApiClient } from "@/lib/api/client";
import { listApprovals } from "@/lib/api/approvals";
import {
  getProductionActivity,
  getProductionOverview,
  getProductionQueue,
} from "@/lib/api/production";
import { listProjects } from "@/lib/api/projects";
import type {
  DailyGoal,
  DashboardData,
  MetricAvailability,
  MetricValue,
} from "@/lib/dashboard/types";
import { initials } from "@/lib/utils";

function live(value: number): MetricValue {
  return { value, availability: "live" };
}

function unavailable(): MetricValue {
  return { value: null, availability: "unavailable" };
}

function restricted(): MetricValue {
  return { value: null, availability: "restricted" };
}

function classifyError(error: unknown): MetricAvailability {
  if (error instanceof ApiError && error.status === 403) return "restricted";
  return "unavailable";
}

const UNAVAILABLE_GOAL: DailyGoal = {
  label: "Approved scripts per day",
  completed: 0,
  target: 0,
  remaining: 0,
  completionPercent: 0,
  weeklyCompleted: 0,
  weeklyTarget: 0,
  availability: "unavailable",
};

/**
 * Live Dashboard adapter — never returns demo/mock rows or silent fallback counts.
 * Failure → unavailable/restricted (value null). Valid API zero → 0.
 */
export async function getDashboardData(api: ApiClient): Promise<DashboardData> {
  let projectsMetric: MetricValue = unavailable();
  let recentProjects: DashboardData["recentProjects"] = [];
  let recentProjectsAvailability: MetricAvailability = "unavailable";

  try {
    const projects = await listProjects(api, { page: 1, page_size: 5 });
    projectsMetric = live(projects.total);
    recentProjects = projects.items.map((project) => ({
      id: project.id,
      projectCode: project.project_code,
      name: project.name,
      category: project.category?.name ?? null,
      status: project.status,
      updatedAt: project.updated_at,
    }));
    recentProjectsAvailability = "live";
  } catch (error) {
    recentProjectsAvailability = classifyError(error);
    projectsMetric =
      recentProjectsAvailability === "restricted" ? restricted() : unavailable();
  }

  let knowledgePacks = unavailable();
  let scripts = unavailable();
  let draftScripts = unavailable();
  let needingRevision = unavailable();
  let pendingReviewsMetric = unavailable();
  let approvedScripts = unavailable();
  let aiRunning = unavailable();
  let aiFailed = unavailable();
  let averageQualityScore = unavailable();
  let staleQualityReviews = unavailable();
  let dailyGoal: DailyGoal = { ...UNAVAILABLE_GOAL };

  try {
    const overview = await getProductionOverview(api);
    knowledgePacks = live(overview.catalog.knowledge_packs);
    scripts = live(overview.catalog.scripts);
    draftScripts = live(overview.catalog.draft_scripts);
    needingRevision = live(overview.quality.scripts_needing_revision);
    pendingReviewsMetric = live(
      overview.stage_counts.pending_human_review ?? 0,
    );
    approvedScripts = live(overview.goals.approved_total);
    aiRunning = live(overview.ai.running);
    aiFailed = live(overview.ai.failed);
    averageQualityScore = {
      value: overview.quality.average_current_score,
      availability: "live",
    };
    staleQualityReviews = live(overview.quality.stale_reviews);
    dailyGoal = {
      label: `${overview.goals.daily_target} approved scripts per day`,
      completed: overview.goals.approved_today,
      target: overview.goals.daily_target,
      remaining: overview.goals.remaining,
      completionPercent: overview.goals.completion_percent,
      weeklyCompleted: overview.goals.approved_this_week,
      weeklyTarget: overview.goals.weekly_target,
      availability: "live",
    };
  } catch (error) {
    const availability = classifyError(error);
    const empty =
      availability === "restricted" ? restricted() : unavailable();
    knowledgePacks = empty;
    scripts = empty;
    draftScripts = empty;
    needingRevision = empty;
    pendingReviewsMetric = empty;
    approvedScripts = empty;
    aiRunning = empty;
    aiFailed = empty;
    averageQualityScore = empty;
    staleQualityReviews = empty;
    dailyGoal = {
      ...UNAVAILABLE_GOAL,
      availability,
    };
  }

  let pendingReviews: DashboardData["pendingReviews"] = [];
  let pendingReviewsAvailability: MetricAvailability = "unavailable";

  try {
    const approvals = await listApprovals(api, {
      page: 1,
      page_size: 5,
      status: "pending",
    });
    pendingReviews = approvals.items.map((item) => ({
      id: item.id,
      title: item.script?.title ?? item.content_version.title,
      versionNumber: item.content_version.version_number,
      status: item.status,
      reviewerInitials: item.reviewed_by
        ? initials(
            `${item.reviewed_by.first_name} ${item.reviewed_by.last_name}`,
          )
        : initials(
            `${item.requested_by.first_name} ${item.requested_by.last_name}`,
          ),
      updatedAt: item.created_at,
      projectCode: item.project.project_code,
      scriptCode: item.script?.script_code ?? null,
    }));
    pendingReviewsAvailability = "live";
  } catch (error) {
    pendingReviewsAvailability = classifyError(error);
  }

  let recentScripts: DashboardData["recentScripts"] = [];
  let recentScriptsAvailability: MetricAvailability = "unavailable";

  try {
    const queue = await getProductionQueue(api, {
      page: 1,
      page_size: 5,
      sort: "updated_at",
    });
    recentScripts = queue.items
      .filter((item) => item.script_id && item.script_title)
      .map((item) => ({
        id: item.script_id as string,
        projectId: item.project_id,
        title: item.script_title as string,
        projectCode: item.project_code,
        status: item.script_status ?? item.production_stage,
        updatedAt: item.updated_at,
      }));
    recentScriptsAvailability = "live";
  } catch (error) {
    recentScriptsAvailability = classifyError(error);
  }

  let recentActivity: DashboardData["recentActivity"] = [];
  let recentActivityAvailability: MetricAvailability = "unavailable";

  try {
    const activity = await getProductionActivity(api, 8);
    if (activity.restricted) {
      recentActivityAvailability = "restricted";
      recentActivity = [];
    } else {
      recentActivityAvailability = "live";
      recentActivity = activity.items.map((item) => ({
        id: item.id,
        action: item.action,
        summary: item.action_label,
        actorName: item.entity_type.replaceAll("_", " "),
        createdAt: item.created_at,
      }));
    }
  } catch (error) {
    recentActivityAvailability = classifyError(error);
  }

  return {
    metrics: {
      projects: projectsMetric,
      knowledgePacks,
      scripts,
      draftScripts,
      needingRevision,
      pendingReviews: pendingReviewsMetric,
      approvedScripts,
      aiRunning,
      aiFailed,
      averageQualityScore,
      staleQualityReviews,
    },
    dailyGoal,
    recentProjects,
    recentProjectsAvailability,
    recentScripts,
    recentScriptsAvailability,
    pendingReviews,
    pendingReviewsAvailability,
    recentActivity,
    recentActivityAvailability,
  };
}
