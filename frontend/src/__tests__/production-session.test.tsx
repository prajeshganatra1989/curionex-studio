import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ProductionSessionPage } from "@/components/production/production-session-page";
import type { ProductionSession } from "@/lib/production/types";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/production/session",
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
  } & Record<string, unknown>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const getProductionSession = vi.fn();

vi.mock("@/lib/api/production", () => ({
  getProductionSession: (...args: unknown[]) => getProductionSession(...args),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "owner@example.com",
      first_name: "Owner",
      last_name: "User",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    api: { baseUrl: "http://test" },
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const activeSession: ProductionSession = {
  today: {
    goal: 2,
    completed: 0,
    estimated_finish: "~24 min remaining on current production",
    current_streak: 0,
  },
  progress: {
    approved_total: 18,
    approved_target: 120,
    remaining: 102,
    completion_percent: 15,
    approved_today: 0,
  },
  current: {
    topic_title: "Why Do We Dream?",
    topic_id: "t1",
    topic_slug: "why-do-we-dream",
    project_id: "p1",
    project_code: "CRX-0001",
    project_name: "Why Do We Dream?",
    script_id: "s1",
    script_title: "Why Do We Dream?",
    production_stage: "discovery_brief",
    stage_label: "Discovery Brief Review",
    next_action: {
      code: "generate_discovery_brief",
      label: "Review Discovery Brief",
      href: "/projects/p1/scripts/s1",
      reason: "Continue drafting",
      blocked: false,
    },
    continue_url: "/projects/p1/scripts/s1",
    wave: 1,
    priority: "A",
    estimated_remaining_steps: 5,
    timeline: [
      { key: "editorial_topic", label: "Editorial Topic", status: "complete" },
      { key: "knowledge_pack", label: "Knowledge Pack", status: "complete" },
      { key: "discovery_brief", label: "Discovery Brief", status: "current" },
      { key: "story_spine", label: "Story Spine", status: "upcoming" },
      { key: "master_script", label: "Master Script", status: "upcoming" },
      { key: "quality_review", label: "Quality Review", status: "upcoming" },
      { key: "version", label: "Version", status: "upcoming" },
      { key: "approval", label: "Approval", status: "upcoming" },
    ],
    sidebar: {
      wave: 1,
      priority: "A",
      estimated_remaining_minutes: 60,
      quality_score: null,
      quality_band: null,
      approval_status: null,
      knowledge_pack_status: "complete",
      knowledge_pack_completion: 100,
      version_status: null,
      reviewer: null,
    },
  },
  upcoming: [
    {
      topic_title: "Why Is Space Silent?",
      topic_id: "t2",
      topic_slug: "why-is-space-silent",
      project_id: "p2",
      project_code: "CRX-0002",
      project_name: "Why Is Space Silent?",
      script_id: null,
      script_title: null,
      production_stage: "idea",
      stage_label: "Idea",
      next_action: {
        code: "create_knowledge_pack",
        label: "Create Knowledge Pack",
        href: "/projects/p2/packs",
        reason: "Start research",
        blocked: false,
      },
      continue_url: "/projects/p2/packs",
      wave: 1,
      priority: "A",
      estimated_remaining_steps: 8,
      timeline: [],
    },
  ],
  previous_completed: null,
  warnings: [],
  empty: false,
  browse_topics_url: "/topics",
  settings: {
    daily_approved_script_target: 2,
    approved_script_target: 120,
  },
};

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

describe("ProductionSessionPage", () => {
  beforeEach(() => {
    pushMock.mockReset();
    getProductionSession.mockReset();
    getProductionSession.mockResolvedValue(activeSession);
  });

  it("renders session counter, current work, timeline, sidebar, and queue", async () => {
    wrap(<ProductionSessionPage />);
    expect(await screen.findByText("Why Do We Dream?")).toBeInTheDocument();
    expect(screen.getByTestId("session-counter")).toBeInTheDocument();
    expect(screen.getByText("18 / 120")).toBeInTheDocument();
    expect(screen.getByTestId("session-timeline")).toBeInTheDocument();
    expect(screen.getByTestId("session-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("session-queue")).toBeInTheDocument();
    expect(screen.getByText("Why Is Space Silent?")).toBeInTheDocument();
  });

  it("continues to the exact deep link", async () => {
    const user = userEvent.setup();
    wrap(<ProductionSessionPage />);
    await screen.findByText("Why Do We Dream?");
    await user.click(screen.getByTestId("session-continue"));
    expect(pushMock).toHaveBeenCalledWith("/projects/p1/scripts/s1");
  });

  it("shows empty state with browse library CTA", async () => {
    getProductionSession.mockResolvedValue({
      ...activeSession,
      empty: true,
      current: null,
      upcoming: [],
    });
    wrap(<ProductionSessionPage />);
    expect(
      await screen.findByText(/all production work completed/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("browse-editorial-library")).toHaveAttribute(
      "href",
      "/topics",
    );
  });
});
