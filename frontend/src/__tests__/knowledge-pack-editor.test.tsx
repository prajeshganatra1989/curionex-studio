import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgePackEditor } from "@/components/knowledge-packs/knowledge-pack-editor";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { KnowledgePackDetail, Project } from "@/lib/api/types";
import { SECTION_ORDER } from "@/lib/knowledge-packs/sections";

const getKnowledgePack = vi.fn();
const getProject = vi.fn();
const updateKnowledgePackSection = vi.fn();
const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({
    projectId: "proj-1",
    knowledgePackId: "pack-1",
  }),
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
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

vi.mock("@/lib/api/projects", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/projects")>(
    "@/lib/api/projects",
  );
  return {
    ...actual,
    getKnowledgePack: (...args: unknown[]) => getKnowledgePack(...args),
    getProject: (...args: unknown[]) => getProject(...args),
    updateKnowledgePackSection: (...args: unknown[]) =>
      updateKnowledgePackSection(...args),
  };
});

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "u1",
      email: "owner@example.com",
      first_name: "Owner",
      last_name: "User",
      is_active: true,
      created_at: "",
      updated_at: "",
    },
    login: vi.fn(),
    logout: vi.fn(),
    api: { baseUrl: "http://test" },
  }),
}));

const project: Project = {
  id: "proj-1",
  project_code: "CRX-0001",
  name: "Black Holes",
  description: null,
  status: "active",
  category_id: null,
  created_by: "u1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  category: null,
  tags: [],
};

function makePack(overrides: Partial<KnowledgePackDetail> = {}): KnowledgePackDetail {
  return {
    id: "pack-1",
    project_id: "proj-1",
    name: "Core Research",
    description: null,
    status: "draft",
    created_by: "u1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    sections: SECTION_ORDER.map((meta, index) => ({
      id: `sec-${meta.key}`,
      knowledge_pack_id: "pack-1",
      section_key: meta.key,
      title: meta.title,
      content: meta.key === "research" ? "Initial research notes" : "",
      position: index + 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    })),
    ...overrides,
  };
}

function wrap(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  );
}

describe("KnowledgePackEditor", () => {
  beforeEach(() => {
    getKnowledgePack.mockReset();
    getProject.mockReset();
    updateKnowledgePackSection.mockReset();
    pushMock.mockReset();
    getProject.mockResolvedValue(project);
    getKnowledgePack.mockResolvedValue(makePack());
    class IO {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("IntersectionObserver", IO);
  });

  it("renders workspace header and all sections", async () => {
    wrap(<KnowledgePackEditor />);
    expect(await screen.findByRole("heading", { name: "Core Research" })).toBeInTheDocument();
    expect(screen.getByText("CRX-0001")).toBeInTheDocument();
    expect(screen.getByText((t) => t.includes("Black Holes"))).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to Project/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate Script/i })).toBeInTheDocument();
    for (const meta of SECTION_ORDER) {
      expect(
        screen.getByRole("heading", { name: meta.title, level: 2 }),
      ).toBeInTheDocument();
    }
    expect(screen.getByDisplayValue("Initial research notes")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    getKnowledgePack.mockReturnValue(new Promise(() => undefined));
    wrap(<KnowledgePackEditor />);
    expect(screen.getByTestId("kp-editor-loading")).toBeInTheDocument();
  });

  it("shows not-found state", async () => {
    getKnowledgePack.mockRejectedValue(new ApiError(404, "Not found"));
    wrap(<KnowledgePackEditor />);
    expect(await screen.findByText("Knowledge Pack not found")).toBeInTheDocument();
  });

  it("tracks dirty state and saves only modified sections", async () => {
    const user = userEvent.setup();
    wrap(<KnowledgePackEditor />);
    await screen.findByDisplayValue("Initial research notes");

    expect(screen.getByTestId("save-status")).toHaveTextContent(/Saved/i);
    const saveButton = screen.getByRole("button", { name: "Save Knowledge Pack" });
    expect(saveButton).toBeDisabled();

    const facts = screen.getByLabelText("Facts content");
    await user.type(facts, "Gravity bends light");
    expect(screen.getByTestId("save-status")).toHaveTextContent("Unsaved changes");
    expect(saveButton).toBeEnabled();

    updateKnowledgePackSection.mockResolvedValue({
      id: "sec-facts",
      knowledge_pack_id: "pack-1",
      section_key: "facts",
      title: "Facts",
      content: "Gravity bends light",
      position: 2,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-03T00:00:00Z",
    });

    await user.click(saveButton);
    await waitFor(() => {
      expect(updateKnowledgePackSection).toHaveBeenCalledTimes(1);
      expect(updateKnowledgePackSection).toHaveBeenCalledWith(
        expect.anything(),
        "pack-1",
        "facts",
        { content: "Gravity bends light" },
      );
    });
    await waitFor(() => {
      expect(screen.getByTestId("save-status")).toHaveTextContent(/Saved/i);
    });
  });

  it("preserves drafts and shows retry on save failure", async () => {
    const user = userEvent.setup();
    wrap(<KnowledgePackEditor />);
    await screen.findByDisplayValue("Initial research notes");
    const facts = screen.getByLabelText("Facts content");
    await user.type(facts, "Keep me");
    updateKnowledgePackSection.mockRejectedValue(new ApiError(500, "Write failed"));
    await user.click(screen.getByRole("button", { name: "Save Knowledge Pack" }));
    expect(await screen.findByText("Write failed")).toBeInTheDocument();
    expect(screen.getByLabelText("Facts content")).toHaveValue("Keep me");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("navigates via section navigator", async () => {
    const user = userEvent.setup();
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    wrap(<KnowledgePackEditor />);
    await screen.findByRole("heading", { name: "Core Research" });
    const nav = screen.getByRole("navigation", {
      name: "Knowledge Pack sections",
    });
    await user.click(within(nav).getByRole("button", { name: /Sources/i }));
    expect(scrollIntoView).toHaveBeenCalled();
  });

  it("opens mobile section drawer", async () => {
    const user = userEvent.setup();
    wrap(<KnowledgePackEditor />);
    await screen.findByRole("heading", { name: "Core Research" });
    await user.click(screen.getByRole("button", { name: "Open section navigator" }));
    expect(await screen.findByRole("dialog", { name: "Sections" })).toBeInTheDocument();
  });

  it("navigates Generate Script to project scripts list", async () => {
    const user = userEvent.setup();
    wrap(<KnowledgePackEditor />);
    await screen.findByRole("heading", { name: "Core Research" });
    await user.click(screen.getByRole("button", { name: /Generate Script/i }));
    expect(pushMock).toHaveBeenCalledWith("/projects/proj-1/scripts");
  });

  it("shows word/character counters and local completion", async () => {
    const { container } = wrap(<KnowledgePackEditor />);
    await screen.findByDisplayValue("Initial research notes");
    expect(screen.getAllByTestId("word-counter").length).toBeGreaterThan(0);
    expect(screen.getAllByTestId("character-counter").length).toBeGreaterThan(0);
    const progress = container.querySelector(
      '[aria-label="Writing progress"]',
    ) as HTMLElement;
    expect(progress).toBeTruthy();
    expect(within(progress).getByText("14%")).toBeInTheDocument();
    expect(within(progress).getByText("1 of 7 sections started")).toBeInTheDocument();
  });

  it("uses responsive three-column layout classes", async () => {
    const { container } = wrap(<KnowledgePackEditor />);
    await screen.findByRole("heading", { name: "Core Research" });
    expect(
      container.querySelector(
        ".xl\\:grid-cols-\\[13rem_minmax\\(0\\,42rem\\)_15rem\\]",
      ),
    ).toBeTruthy();
    expect(container.querySelector(".hidden.xl\\:block")).toBeTruthy();
    expect(container.querySelector(".hidden.lg\\:block")).toBeTruthy();
  });
});
