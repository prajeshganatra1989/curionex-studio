import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

const listProjects = vi.fn();
const listApprovals = vi.fn();
const getProductionOverview = vi.fn();
const getProductionQueue = vi.fn();
const getProductionActivity = vi.fn();

vi.mock("@/lib/api/projects", () => ({
  listProjects: (...args: unknown[]) => listProjects(...args),
}));

vi.mock("@/lib/api/approvals", () => ({
  listApprovals: (...args: unknown[]) => listApprovals(...args),
}));

vi.mock("@/lib/api/production", () => ({
  getProductionOverview: (...args: unknown[]) => getProductionOverview(...args),
  getProductionQueue: (...args: unknown[]) => getProductionQueue(...args),
  getProductionActivity: (...args: unknown[]) => getProductionActivity(...args),
}));

import { getDashboardData } from "@/lib/dashboard/data";

describe("getDashboardData", () => {
  beforeEach(() => {
    listProjects.mockReset();
    listApprovals.mockReset();
    getProductionOverview.mockReset();
    getProductionQueue.mockReset();
    getProductionActivity.mockReset();

    listProjects.mockResolvedValue({
      items: [
        {
          id: "p1",
          project_code: "CRX-1",
          name: "Real Project",
          category: null,
          status: "active",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
      page: 1,
      page_size: 5,
    });
    listApprovals.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 5,
    });
    getProductionQueue.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 5,
    });
    getProductionActivity.mockResolvedValue({
      items: [],
      restricted: false,
    });
  });

  it("uses production overview for live production metrics", async () => {
    getProductionOverview.mockResolvedValue({
      goals: {
        approved_target: 120,
        approved_total: 10,
        remaining: 110,
        completion_percent: 8.3,
        daily_target: 2,
        approved_today: 0,
        weekly_target: 14,
        approved_this_week: 0,
        projected_days_remaining: null,
      },
      stage_counts: { pending_human_review: 3 },
      ai: {
        queued: 0,
        running: 1,
        failed: 2,
        completed_today: 0,
        estimated_cost_today: 0,
        estimated_cost_this_week: 0,
      },
      quality: {
        average_current_score: 80,
        scripts_needing_revision: 4,
        stale_reviews: 1,
        high_risk_fact_flags: 0,
      },
      catalog: {
        projects: 1,
        knowledge_packs: 2,
        scripts: 5,
        draft_scripts: 3,
      },
    });

    const data = await getDashboardData({} as never);

    expect(data.metrics.projects).toEqual({ value: 1, availability: "live" });
    expect(data.metrics.knowledgePacks).toEqual({
      value: 2,
      availability: "live",
    });
    expect(data.metrics.scripts).toEqual({ value: 5, availability: "live" });
    expect(data.metrics.draftScripts).toEqual({
      value: 3,
      availability: "live",
    });
    expect(data.metrics.approvedScripts).toEqual({
      value: 10,
      availability: "live",
    });
    expect(data.metrics.needingRevision).toEqual({
      value: 4,
      availability: "live",
    });
    expect(data.metrics.aiRunning).toEqual({ value: 1, availability: "live" });
    expect(data.metrics.pendingReviews).toEqual({
      value: 3,
      availability: "live",
    });
    expect(data.dailyGoal.availability).toBe("live");
    expect(data.dailyGoal.completed).toBe(0);
    expect(data.dailyGoal.target).toBe(2);
    expect(data.recentProjects[0]?.name).toBe("Real Project");
    expect(JSON.stringify(data)).not.toMatch(
      /Black Holes|Event Horizon|CRX-0001|Demo/,
    );
  });

  it("keeps valid zeros as live zeros", async () => {
    listProjects.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 5,
    });
    getProductionOverview.mockResolvedValue({
      goals: {
        approved_target: 120,
        approved_total: 0,
        remaining: 120,
        completion_percent: 0,
        daily_target: 2,
        approved_today: 0,
        weekly_target: 14,
        approved_this_week: 0,
        projected_days_remaining: null,
      },
      stage_counts: { pending_human_review: 0 },
      ai: {
        queued: 0,
        running: 0,
        failed: 0,
        completed_today: 0,
        estimated_cost_today: 0,
        estimated_cost_this_week: 0,
      },
      quality: {
        average_current_score: null,
        scripts_needing_revision: 0,
        stale_reviews: 0,
        high_risk_fact_flags: 0,
      },
      catalog: {
        projects: 0,
        knowledge_packs: 0,
        scripts: 0,
        draft_scripts: 0,
      },
    });

    const data = await getDashboardData({} as never);
    expect(data.metrics.projects).toEqual({ value: 0, availability: "live" });
    expect(data.metrics.scripts).toEqual({ value: 0, availability: "live" });
    expect(data.metrics.approvedScripts).toEqual({
      value: 0,
      availability: "live",
    });
    expect(data.metrics.averageQualityScore).toEqual({
      value: null,
      availability: "live",
    });
  });

  it("does not fall back to demo counts on overview failure", async () => {
    getProductionOverview.mockRejectedValue(new ApiError(500, "boom"));
    getProductionQueue.mockRejectedValue(new ApiError(500, "boom"));

    const data = await getDashboardData({} as never);

    expect(data.metrics.approvedScripts).toEqual({
      value: null,
      availability: "unavailable",
    });
    expect(data.metrics.needingRevision.value).toBeNull();
    expect(data.metrics.knowledgePacks.value).toBeNull();
    expect(data.dailyGoal.availability).toBe("unavailable");
    expect(data.recentScriptsAvailability).toBe("unavailable");
    expect(data.metrics.projects).toEqual({ value: 1, availability: "live" });
  });

  it("maps 403 to restricted without inventing values", async () => {
    listProjects.mockRejectedValue(new ApiError(403, "forbidden"));
    getProductionOverview.mockRejectedValue(new ApiError(403, "forbidden"));
    listApprovals.mockRejectedValue(new ApiError(403, "forbidden"));
    getProductionQueue.mockRejectedValue(new ApiError(403, "forbidden"));
    getProductionActivity.mockResolvedValue({
      items: [],
      restricted: true,
    });

    const data = await getDashboardData({} as never);

    expect(data.metrics.projects.availability).toBe("restricted");
    expect(data.metrics.approvedScripts.availability).toBe("restricted");
    expect(data.pendingReviewsAvailability).toBe("restricted");
    expect(data.recentActivityAvailability).toBe("restricted");
    expect(data.metrics.projects.value).toBeNull();
  });
});
