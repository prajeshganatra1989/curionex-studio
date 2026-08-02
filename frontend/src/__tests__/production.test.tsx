import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { GoalHero } from "@/components/production/goal-hero";
import { QueueView } from "@/components/production/queue-view";
import {
  QuickFilters,
  DEFAULT_FILTERS,
  type ProductionFilterState,
} from "@/components/production/quick-filters";
import { ProductionSettingsDialog } from "@/components/production/production-settings-dialog";
import { ProductionPage } from "@/components/production/production-page";
import { ToastProvider } from "@/components/ui/toast";
import type {
  ProductionGoalsSummary,
  ProductionOverview,
  ProductionQueueItem,
  ProductionSettings,
} from "@/lib/production/types";

const replaceMock = vi.fn();
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
  usePathname: () => "/production",
  useSearchParams: () => searchParams,
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const overviewMock = vi.fn();
const queueMock = vi.fn();
const metricsMock = vi.fn();
const activityMock = vi.fn();
const settingsMock = vi.fn();
const updateSettingsMock = vi.fn();

vi.mock("@/lib/production/hooks", () => ({
  productionKeys: {
    all: ["production"],
    overview: () => ["production", "overview"],
    queue: (params: unknown) => ["production", "queue", params],
    metrics: (range: string) => ["production", "metrics", range],
    activity: (limit: number) => ["production", "activity", limit],
    settings: () => ["production", "settings"],
  },
  useProductionOverview: () => overviewMock(),
  useProductionQueue: () => queueMock(),
  useProductionMetrics: () => metricsMock(),
  useProductionActivity: () => activityMock(),
  useProductionSettings: () => settingsMock(),
  useUpdateProductionSettings: () => ({
    mutateAsync: updateSettingsMock,
    isPending: false,
  }),
}));

vi.mock("@/lib/projects/hooks", () => ({
  useCategories: () => ({ data: [] }),
  useTags: () => ({ data: [] }),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "prajesh@example.com",
      first_name: "Prajesh",
      last_name: "G",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

const sampleGoals: ProductionGoalsSummary = {
  approved_target: 120,
  approved_total: 25,
  remaining: 95,
  completion_percent: 20.83,
  daily_target: 2,
  approved_today: 1,
  weekly_target: 14,
  approved_this_week: 5,
  projected_days_remaining: 47.5,
};

const sampleItem: ProductionQueueItem = {
  script_id: "s1",
  project_id: "p1",
  project_code: "CRX-0001",
  project_name: "Black Holes",
  script_code: "CRX-0001-S01",
  script_title: "Event Horizon",
  script_status: "draft",
  production_stage: "needs_revision",
  next_action: {
    code: "fix_quality_issues",
    label: "Fix Quality Issues",
    href: "/projects/p1/scripts/s1/quality-reviews/g1",
    reason: "Latest quality review recommends revision.",
    blocked: false,
  },
  knowledge_pack_id: "kp1",
  knowledge_pack_completion: 80,
  documents: {
    discovery_brief: "complete",
    story_spine: "complete",
    master_script: "complete",
  },
  quality: {
    score: 62,
    band: "needs_refinement",
    stale: false,
    recommendation: "revise",
    generation_id: "g1",
    high_risk_facts: 0,
  },
  workflow: { stage: null, status: null, active_version_id: null },
  approval: { status: null, approval_id: null },
  ai_job: { status: "completed", job_id: "j1", purpose: "quality", error_message: null },
  updated_at: new Date().toISOString(),
};

const sampleOverview: ProductionOverview = {
  goals: sampleGoals,
  stage_counts: {
    idea: 0,
    research: 1,
    discovery_brief: 0,
    story_spine: 0,
    master_script: 0,
    quality_review: 0,
    needs_revision: 1,
    ready_for_version: 0,
    version_created: 0,
    pending_human_review: 0,
    approved: 25,
    blocked: 0,
    archived: 0,
  },
  ai: {
    queued: 0,
    running: 1,
    failed: 0,
    completed_today: 3,
    estimated_cost_today: 0.42,
    estimated_cost_this_week: 2.1,
  },
  quality: {
    average_current_score: 71,
    scripts_needing_revision: 1,
    stale_reviews: 0,
    high_risk_fact_flags: 0,
  },
  catalog: {
    projects: 3,
    knowledge_packs: 4,
    scripts: 7,
    draft_scripts: 2,
  },
};

const sampleSettings: ProductionSettings = {
  id: "settings-1",
  approved_script_target: 120,
  daily_approved_script_target: 2,
  weekly_approved_script_target: 14,
  updated_at: new Date().toISOString(),
  updated_by: null,
};

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  );
}

describe("GoalHero", () => {
  it("renders progress, daily/weekly targets, and milestone badges", () => {
    wrap(<GoalHero goals={sampleGoals} />);
    expect(screen.getByTestId("approved-total")).toHaveTextContent("25");
    expect(screen.getByTestId("approved-target")).toHaveTextContent("120");
    expect(screen.getByTestId("daily-goal")).toHaveTextContent("1 / 2");
    expect(screen.getByTestId("weekly-goal")).toHaveTextContent("5 / 14");
    const milestones = screen.getByTestId("milestones");
    expect(within(milestones).getByText("10")).toBeInTheDocument();
    expect(within(milestones).getByText("25")).toBeInTheDocument();
    expect(within(milestones).getByText("120")).toBeInTheDocument();
  });
});

describe("QueueView", () => {
  it("renders queue items with next-action href from backend", () => {
    wrap(
      <QueueView
        items={[sampleItem]}
        page={1}
        pageSize={20}
        total={1}
        isLoading={false}
        isError={false}
        onPageChange={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByText("Event Horizon")).toBeInTheDocument();
    expect(screen.getByText("Needs Revision")).toBeInTheDocument();
    const action = screen.getByTestId("next-action");
    expect(action).toHaveAttribute(
      "href",
      "/projects/p1/scripts/s1/quality-reviews/g1",
    );
    expect(action).toHaveTextContent("Fix Quality Issues");
    // Quality is advisory — AI completed must not read as Approved
    expect(screen.queryByText(/^Approved$/)).not.toBeInTheDocument();
  });

  it("shows empty state", () => {
    wrap(
      <QueueView
        items={[]}
        page={1}
        pageSize={20}
        total={0}
        isLoading={false}
        isError={false}
        onPageChange={vi.fn()}
        onRetry={vi.fn()}
        emptyTitle="Nothing here"
      />,
    );
    expect(screen.getByTestId("queue-empty")).toBeInTheDocument();
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });
});

describe("QuickFilters", () => {
  it("toggles quick chips and opens advanced drawer", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const filters: ProductionFilterState = { ...DEFAULT_FILTERS };
    wrap(
      <QuickFilters
        filters={filters}
        searchInput=""
        onSearchInputChange={vi.fn()}
        onChange={onChange}
        onReset={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: /pending approval/i }));
    expect(onChange).toHaveBeenCalledWith({ pending_approval: true });
    await user.click(screen.getByTestId("open-advanced-filters"));
    expect(screen.getByTestId("advanced-filters")).toBeInTheDocument();
    expect(screen.getByLabelText("Stage")).toBeInTheDocument();
  });
});

describe("ProductionSettingsDialog", () => {
  beforeEach(() => {
    settingsMock.mockReturnValue({
      data: sampleSettings,
      isLoading: false,
      isError: false,
      error: null,
    });
    updateSettingsMock.mockReset();
    updateSettingsMock.mockResolvedValue(sampleSettings);
  });

  it("loads settings and submits with RHF + Zod", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    wrap(<ProductionSettingsDialog open onClose={onClose} />);
    expect(screen.getByTestId("production-settings-form")).toBeInTheDocument();
    const daily = screen.getByLabelText(/daily approved target/i);
    await user.clear(daily);
    await user.type(daily, "3");
    await user.click(screen.getByRole("button", { name: /^save$/i }));
    expect(updateSettingsMock).toHaveBeenCalled();
    const payload = updateSettingsMock.mock.calls[0][0];
    expect(payload.daily_approved_script_target).toBe(3);
  });
});

describe("ProductionPage", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    replaceMock.mockReset();
    overviewMock.mockReturnValue({
      data: sampleOverview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    queueMock.mockReturnValue({
      data: { items: [sampleItem], page: 1, page_size: 20, total: 1 },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    metricsMock.mockReturnValue({
      data: {
        range: "7d",
        scripts_approved: 5,
        versions_created: 2,
        quality_reviews_completed: 4,
        average_quality_score: 70,
        ai_jobs_completed: 8,
        ai_jobs_failed: 0,
        estimated_ai_cost: 1.2,
        average_days_to_approval: 3.5,
      },
      isLoading: false,
    });
    activityMock.mockReturnValue({
      data: { items: [], restricted: false },
      isLoading: false,
    });
    settingsMock.mockReturnValue({
      data: sampleSettings,
      isLoading: false,
      isError: false,
      error: null,
    });
  });

  it("renders production workspace with goal hero and queue", async () => {
    wrap(<ProductionPage />);
    expect(await screen.findByTestId("goal-hero")).toBeInTheDocument();
    expect(screen.getByTestId("queue-view")).toBeInTheDocument();
    expect(screen.getByTestId("ai-ops-panel")).toBeInTheDocument();
    expect(screen.getByText(/never marks scripts Approved/i)).toBeInTheDocument();
  });

  it("shows empty catalog state when there are no projects/scripts", async () => {
    overviewMock.mockReturnValue({
      data: {
        ...sampleOverview,
        stage_counts: Object.fromEntries(
          Object.keys(sampleOverview.stage_counts).map((k) => [k, 0]),
        ),
        goals: { ...sampleGoals, approved_total: 0 },
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    queueMock.mockReturnValue({
      data: { items: [], page: 1, page_size: 20, total: 0 },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    wrap(<ProductionPage />);
    expect(await screen.findByTestId("production-empty")).toBeInTheDocument();
    expect(screen.getByText(/no projects in production yet/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /create project/i }),
    ).toHaveAttribute("href", "/projects");
  });

  it("syncs pending approval filter to the URL", async () => {
    const user = userEvent.setup();
    wrap(<ProductionPage />);
    await user.click(screen.getByRole("button", { name: /pending approval/i }));
    expect(replaceMock).toHaveBeenCalled();
    const url = String(replaceMock.mock.calls.at(-1)?.[0] ?? "");
    expect(url).toContain("pending_approval=1");
  });
});
