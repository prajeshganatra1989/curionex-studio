import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  DashboardPage,
  DASHBOARD_QUERY_KEY,
} from "@/components/dashboard/dashboard-page";
import type { DashboardData, MetricValue } from "@/lib/dashboard/types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/dashboard",
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

const getDashboardData = vi.fn();

vi.mock("@/lib/dashboard/data", () => ({
  getDashboardData: (...args: unknown[]) => getDashboardData(...args),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "prajesh@example.com",
      first_name: "Prajesh",
      last_name: "Ganatra",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

function live(value: number | null): MetricValue {
  return { value, availability: "live" };
}

function unavailable(): MetricValue {
  return { value: null, availability: "unavailable" };
}

function restricted(): MetricValue {
  return { value: null, availability: "restricted" };
}

const liveDashboard: DashboardData = {
  metrics: {
    projects: live(3),
    knowledgePacks: live(4),
    scripts: live(7),
    draftScripts: live(2),
    needingRevision: live(4),
    pendingReviews: live(5),
    approvedScripts: live(31),
    aiRunning: live(2),
    aiFailed: live(1),
    averageQualityScore: live(71),
    staleQualityReviews: live(0),
  },
  dailyGoal: {
    label: "2 approved scripts per day",
    completed: 1,
    target: 2,
    remaining: 89,
    completionPercent: 25.8,
    weeklyCompleted: 5,
    weeklyTarget: 14,
    availability: "live",
  },
  recentProjects: [
    {
      id: "live-1",
      projectCode: "CRX-0099",
      name: "Live Project Alpha",
      category: "Science",
      status: "active",
      updatedAt: new Date().toISOString(),
    },
  ],
  recentProjectsAvailability: "live",
  recentScripts: [
    {
      id: "s1",
      projectId: "live-1",
      title: "Live Script",
      projectCode: "CRX-0099",
      status: "draft",
      updatedAt: new Date().toISOString(),
    },
  ],
  recentScriptsAvailability: "live",
  pendingReviews: [
    {
      id: "r1",
      title: "Pending Script",
      versionNumber: 2,
      status: "pending",
      reviewerInitials: "PG",
      updatedAt: new Date().toISOString(),
      projectCode: "CRX-0099",
    },
  ],
  pendingReviewsAvailability: "live",
  recentActivity: [
    {
      id: "a1",
      action: "approval.approved",
      summary: "Script approved",
      actorName: "script",
      createdAt: new Date().toISOString(),
    },
  ],
  recentActivityAvailability: "live",
};

describe("DashboardPage", () => {
  beforeEach(() => {
    getDashboardData.mockReset();
    getDashboardData.mockResolvedValue(liveDashboard);
  });

  it("shows live overview metrics without demo badges or dummy rows", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );

    expect(await screen.findByText(/Prajesh/)).toBeInTheDocument();
    expect(screen.getByText("Approved Scripts")).toBeInTheDocument();
    expect(screen.getByText("31")).toBeInTheDocument();
    expect(screen.getByText("Needs Revision")).toBeInTheDocument();
    expect(screen.getByText("AI Jobs Running")).toBeInTheDocument();
    expect(screen.getByTestId("daily-goal-card")).toHaveAttribute(
      "data-availability",
      "live",
    );
    expect(screen.getByText(/1 \/ 2/)).toBeInTheDocument();
    expect(screen.getByText("Live Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("Live Script")).toBeInTheDocument();
    expect(screen.getByText("Pending Script")).toBeInTheDocument();
    expect(screen.getByText("Script approved")).toBeInTheDocument();
    expect(screen.queryByText("Demo")).not.toBeInTheDocument();
    expect(screen.queryByText("Black Holes Explained")).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /open production mode/i }),
    ).toHaveAttribute("href", "/production");
  });

  it("shows unavailable labels on API failure payload", async () => {
    getDashboardData.mockResolvedValue({
      ...liveDashboard,
      metrics: {
        projects: unavailable(),
        knowledgePacks: unavailable(),
        scripts: unavailable(),
        draftScripts: unavailable(),
        needingRevision: unavailable(),
        pendingReviews: unavailable(),
        approvedScripts: unavailable(),
        aiRunning: unavailable(),
        aiFailed: unavailable(),
        averageQualityScore: unavailable(),
        staleQualityReviews: unavailable(),
      },
      dailyGoal: { ...liveDashboard.dailyGoal, availability: "unavailable" },
      recentProjects: [],
      recentProjectsAvailability: "unavailable",
      recentScripts: [],
      recentScriptsAvailability: "unavailable",
      pendingReviews: [],
      pendingReviewsAvailability: "unavailable",
      recentActivity: [],
      recentActivityAvailability: "unavailable",
    });

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );

    expect(await screen.findAllByText("Unavailable")).not.toHaveLength(0);
    expect(screen.getAllByText(/temporarily unavailable/i).length).toBeGreaterThan(0);
    expect(screen.queryByText("31")).not.toBeInTheDocument();
  });

  it("shows restricted states", async () => {
    getDashboardData.mockResolvedValue({
      ...liveDashboard,
      metrics: {
        ...liveDashboard.metrics,
        pendingReviews: restricted(),
      },
      pendingReviews: [],
      pendingReviewsAvailability: "restricted",
      recentActivity: [],
      recentActivityAvailability: "restricted",
    });

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Restricted")).toBeInTheDocument();
    expect(screen.getByText(/access restricted/i)).toBeInTheDocument();
    expect(screen.getByText(/activity restricted/i)).toBeInTheDocument();
  });

  it("displays valid zero counts as 0", async () => {
    getDashboardData.mockResolvedValue({
      ...liveDashboard,
      metrics: {
        ...liveDashboard.metrics,
        projects: live(0),
        scripts: live(0),
        approvedScripts: live(0),
        needingRevision: live(0),
        pendingReviews: live(0),
        aiRunning: live(0),
        draftScripts: live(0),
        knowledgePacks: live(0),
        aiFailed: live(0),
        staleQualityReviews: live(0),
        averageQualityScore: live(null),
      },
      recentProjects: [],
      recentScripts: [],
      pendingReviews: [],
      recentActivity: [],
    });

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );

    await screen.findByText("Projects");
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(5);
  });

  it("refresh invalidates the dashboard query", async () => {
    const user = userEvent.setup();
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(client, "invalidateQueries");
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );
    await screen.findByText("Live Project Alpha");
    await user.click(screen.getByTestId("dashboard-refresh"));
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: DASHBOARD_QUERY_KEY,
      });
    });
    expect(getDashboardData.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
