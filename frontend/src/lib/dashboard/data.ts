import { ApiError, type ApiClient } from "@/lib/api/client";
import { listApprovals } from "@/lib/api/approvals";
import { listProjects } from "@/lib/api/projects";
import type { DashboardData } from "@/lib/dashboard/types";
import { initials } from "@/lib/utils";

/**
 * Isolated deterministic mock dashboard payload for modules that are not
 * live yet. Components must not hard-code these values — load via getDashboardData().
 *
 * Live in Sprint 2:
 * - Projects metric (list total)
 * - Recent Projects panel
 *
 * Live in Sprint 3:
 * - Pending Reviews metric + panel (GET /approvals?status=pending)
 *
 * Still demo:
 * - Knowledge Packs / Scripts / Drafts / Approved metrics
 * - Daily goal
 * - Recent Scripts / Activity
 */
export const DEMO_DASHBOARD: DashboardData = {
  metrics: {
    projects: 12,
    knowledgePacks: 28,
    scripts: 64,
    draftScripts: 18,
    pendingReviews: 5,
    approvedScripts: 31,
    isDemo: true,
    projectsLive: false,
    pendingReviewsLive: false,
  },
  dailyGoal: {
    label: "2 videos per day",
    completed: 1,
    target: 2,
    isDemo: true,
  },
  recentProjects: [
    {
      id: "p1",
      projectCode: "CRX-0001",
      name: "Black Holes Explained",
      category: "Science",
      status: "active",
      updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "p2",
      projectCode: "CRX-0002",
      name: "History of Timekeeping",
      category: "History",
      status: "in_progress",
      updatedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "p3",
      projectCode: "CRX-0003",
      name: "Ocean Currents",
      category: "Earth",
      status: "draft",
      updatedAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
    },
  ],
  recentProjectsLive: false,
  recentScripts: [
    {
      id: "s1",
      title: "Event Horizon Walkthrough",
      projectCode: "CRX-0001",
      status: "in_review",
      updatedAt: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
    },
    {
      id: "s2",
      title: "Atomic Clocks Story Spine",
      projectCode: "CRX-0002",
      status: "draft",
      updatedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "s3",
      title: "Gulf Stream Master Script",
      projectCode: "CRX-0003",
      status: "approved",
      updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    },
  ],
  pendingReviews: [
    {
      id: "r1",
      title: "Event Horizon Walkthrough",
      versionNumber: 3,
      status: "pending",
      reviewerInitials: "PG",
      updatedAt: new Date(Date.now() - 55 * 60 * 1000).toISOString(),
      projectCode: "CRX-0001",
      scriptCode: "CRX-0001-S01",
    },
    {
      id: "r2",
      title: "Supernova Remnants",
      versionNumber: 1,
      status: "pending",
      reviewerInitials: null,
      updatedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      projectCode: "CRX-0002",
      scriptCode: "CRX-0002-S01",
    },
  ],
  pendingReviewsLive: false,
  pendingReviewsRestricted: false,
  recentActivity: [
    {
      id: "a1",
      action: "script.document_updated",
      summary: "Story Spine updated",
      actorName: "You",
      createdAt: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    },
    {
      id: "a2",
      action: "approval.approved",
      summary: "Script approved",
      actorName: "Reviewer",
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "a3",
      action: "content_version.created",
      summary: "Version created",
      actorName: "You",
      createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: "a4",
      action: "knowledge_pack.section_updated",
      summary: "Knowledge Pack edited",
      actorName: "You",
      createdAt: new Date(Date.now() - 9 * 60 * 60 * 1000).toISOString(),
    },
  ],
  activityRestricted: false,
};

export async function getDashboardData(api: ApiClient): Promise<DashboardData> {
  const projects = await listProjects(api, { page: 1, page_size: 5 });

  let pendingReviews = DEMO_DASHBOARD.pendingReviews;
  let pendingReviewsLive = false;
  let pendingReviewsRestricted = false;
  let pendingReviewsTotal = DEMO_DASHBOARD.metrics.pendingReviews;

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
    pendingReviewsTotal = approvals.total;
    pendingReviewsLive = true;
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) {
      pendingReviews = [];
      pendingReviewsRestricted = true;
      pendingReviewsTotal = 0;
      pendingReviewsLive = true;
    }
  }

  const metricsStillDemo = true; // KP / Scripts / Approved metrics remain demo-backed.

  return {
    ...DEMO_DASHBOARD,
    metrics: {
      ...DEMO_DASHBOARD.metrics,
      projects: projects.total,
      projectsLive: true,
      pendingReviews: pendingReviewsTotal,
      pendingReviewsLive,
      isDemo: metricsStillDemo,
    },
    recentProjects: projects.items.map((project) => ({
      id: project.id,
      projectCode: project.project_code,
      name: project.name,
      category: project.category?.name ?? null,
      status: project.status,
      updatedAt: project.updated_at,
    })),
    recentProjectsLive: true,
    pendingReviews,
    pendingReviewsLive,
    pendingReviewsRestricted,
  };
}
