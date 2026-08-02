import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { TopicsPage } from "@/components/editorial/topics-page";
import { ToastProvider } from "@/components/ui/toast";
import type { EditorialTopic } from "@/lib/editorial/types";

const replaceMock = vi.fn();
const pushMock = vi.fn();
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  usePathname: () => "/topics",
  useSearchParams: () => searchParams,
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

const listEditorialTopics = vi.fn();
const createProjectFromTopic = vi.fn();

vi.mock("@/lib/api/editorial", () => ({
  listEditorialTopics: (...args: unknown[]) => listEditorialTopics(...args),
  createProjectFromTopic: (...args: unknown[]) => createProjectFromTopic(...args),
  getEditorialTopicSummary: vi.fn(),
  createEditorialTopic: vi.fn(),
  archiveEditorialTopic: vi.fn(),
  getEditorialTopic: vi.fn(),
  updateEditorialTopic: vi.fn(),
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

vi.mock("@/lib/projects/hooks", () => ({
  useCategories: () => ({ data: [] }),
  useTags: () => ({ data: [] }),
  useCreateCategory: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreateTag: () => ({ mutateAsync: vi.fn(), isPending: false }),
  projectKeys: { all: ["projects"] },
}));

const sampleTopic: EditorialTopic = {
  id: "t1",
  slug: "why-is-space-silent",
  title: "Why Is Space Silent?",
  description: "Vacuum cannot carry sound waves.",
  category: "Space",
  status: "idea",
  difficulty: "easy",
  evergreen_score: 88,
  curiosity_score: 90,
  viral_potential: "high",
  estimated_duration_seconds: 45,
  target_audience: "Curious adults",
  source: "curionex-evergreen-v1",
  notes: null,
  linked_project_id: null,
  published_video_url: null,
  is_featured: true,
  priority: "A",
  production_wave: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  linked_project: null,
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

describe("TopicsPage", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    replaceMock.mockReset();
    pushMock.mockReset();
    listEditorialTopics.mockReset();
    createProjectFromTopic.mockReset();
    listEditorialTopics.mockResolvedValue({
      items: [sampleTopic],
      page: 1,
      page_size: 20,
      total: 1,
    });
  });

  it("renders topic list with status badges and create project action", async () => {
    wrap(<TopicsPage />);
    expect(await screen.findByText("Why Is Space Silent?")).toBeInTheDocument();
    expect(screen.getAllByText("Space").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText("Featured")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create project/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/idea/i).length).toBeGreaterThanOrEqual(1);
  });

  it("updates filters in the URL", async () => {
    const user = userEvent.setup();
    wrap(<TopicsPage />);
    await screen.findByText("Why Is Space Silent?");
    await user.selectOptions(screen.getByLabelText(/filter by category/i), "Space");
    expect(replaceMock).toHaveBeenCalled();
    const last = replaceMock.mock.calls.at(-1)?.[0] as string;
    expect(last).toContain("category=Space");
  });

  it("updates priority and wave filters in the URL", async () => {
    const user = userEvent.setup();
    wrap(<TopicsPage />);
    await screen.findByText("Why Is Space Silent?");
    await user.selectOptions(screen.getByLabelText(/filter by priority/i), "A");
    expect(replaceMock).toHaveBeenCalled();
    const priorityCall = replaceMock.mock.calls.at(-1)?.[0] as string;
    expect(priorityCall).toContain("priority=A");
    await user.selectOptions(
      screen.getByLabelText(/filter by production wave/i),
      "1",
    );
    const waveCall = replaceMock.mock.calls.at(-1)?.[0] as string;
    expect(waveCall).toContain("production_wave=1");
  });

  it("shows empty state when no topics match", async () => {
    listEditorialTopics.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    });
    wrap(<TopicsPage />);
    expect(await screen.findByText(/no topics match/i)).toBeInTheDocument();
  });

  it("opens create project modal from topic action", async () => {
    const user = userEvent.setup();
    wrap(<TopicsPage />);
    await screen.findByText("Why Is Space Silent?");
    await user.click(screen.getByRole("button", { name: /create project/i }));
    expect(
      await screen.findByRole("heading", { name: /create project from topic/i }),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("Why Is Space Silent?")).toBeInTheDocument();
  });
});
