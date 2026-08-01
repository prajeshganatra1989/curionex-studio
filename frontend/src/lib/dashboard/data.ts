import type { DashboardData } from "@/lib/dashboard/types";

/**
 * Isolated deterministic mock dashboard payload.
 * Components must not hard-code these values — load via getDashboardData().
 *
 * TODO: Wire to live APIs:
 * - projects list/count
 * - knowledge packs count
 * - scripts / statuses
 * - approvals pending
 * - audit.view activity feed
 * - future daily publishing goal tracker
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
    },
    {
      id: "r2",
      title: "Supernova Remnants",
      versionNumber: 1,
      status: "pending",
      reviewerInitials: null,
      updatedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    },
  ],
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

export async function getDashboardData(): Promise<DashboardData> {
  // Frontend-first: return isolated demo data.
  // Later: merge live counts from efficient APIs when endpoints exist.
  return DEMO_DASHBOARD;
}
