import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { DashboardPage } from "@/components/dashboard/dashboard-page";
import type { DashboardData } from "@/lib/dashboard/types";

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

const liveDashboard: DashboardData = {
  metrics: {
    projects: 3,
    knowledgePacks: 28,
    scripts: 64,
    draftScripts: 18,
    pendingReviews: 5,
    approvedScripts: 31,
    isDemo: true,
    projectsLive: true,
  },
  dailyGoal: {
    label: "2 videos per day",
    completed: 1,
    target: 2,
    isDemo: true,
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
  recentProjectsLive: true,
  recentScripts: [
    {
      id: "s1",
      title: "Demo Script",
      projectCode: "CRX-0001",
      status: "draft",
      updatedAt: new Date().toISOString(),
    },
  ],
  pendingReviews: [],
  recentActivity: [],
  activityRestricted: false,
};

describe("DashboardPage", () => {
  beforeEach(() => {
    getDashboardData.mockResolvedValue(liveDashboard);
  });

  it("shows greeting and live project metric/data", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );
    expect(await screen.findByText(/Prajesh/)).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Live Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("CRX-0099")).toBeInTheDocument();
    expect(screen.getByText("Mixed live + demo")).toBeInTheDocument();
    expect(screen.getAllByText("Demo").length).toBeGreaterThan(0);
    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Projects" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Scripts" })).toBeInTheDocument();
  });
});
