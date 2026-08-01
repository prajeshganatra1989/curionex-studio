import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectScriptsPage } from "@/components/scripts/project-scripts-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";

const pushMock = vi.fn();
const listProjectScripts = vi.fn();
const listProjectKnowledgePacks = vi.fn();
const createScript = vi.fn();
const archiveScript = vi.fn();
const getWorkflowStatus = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ projectId: "proj-1" }),
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

vi.mock("@/lib/api/projects", () => ({
  listProjectScripts: (...args: unknown[]) => listProjectScripts(...args),
  listProjectKnowledgePacks: (...args: unknown[]) =>
    listProjectKnowledgePacks(...args),
  createScript: (...args: unknown[]) => createScript(...args),
  archiveScript: (...args: unknown[]) => archiveScript(...args),
  getWorkflowStatus: (...args: unknown[]) => getWorkflowStatus(...args),
}));

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

const scriptItem = {
  id: "sc-1",
  project_id: "proj-1",
  knowledge_pack_id: "kp-1",
  script_code: "CRX-0001-S01",
  title: "Event Horizon",
  description: null,
  status: "draft",
  content_version_id: null,
  created_by: "u1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

describe("ProjectScriptsPage", () => {
  beforeEach(() => {
    pushMock.mockReset();
    listProjectScripts.mockReset();
    listProjectKnowledgePacks.mockReset();
    createScript.mockReset();
    archiveScript.mockReset();
    getWorkflowStatus.mockReset();
    listProjectKnowledgePacks.mockResolvedValue({
      items: [
        {
          id: "kp-1",
          project_id: "proj-1",
          name: "Core Facts",
          description: null,
          status: "draft",
          created_by: "u1",
          created_at: "",
          updated_at: "",
        },
      ],
      page: 1,
      page_size: 100,
      total: 1,
    });
    getWorkflowStatus.mockResolvedValue({
      script_id: "sc-1",
      stage: "workspace",
      status: "active",
      active_version: null,
      latest_version: null,
      approved_version: null,
      pending_approval: null,
    });
  });

  it("renders project scripts page", async () => {
    listProjectScripts.mockResolvedValue({
      items: [scriptItem],
      page: 1,
      page_size: 20,
      total: 1,
    });
    wrap(<ProjectScriptsPage />);
    expect(await screen.findByRole("heading", { name: "Scripts" })).toBeInTheDocument();
    expect(await screen.findAllByText("Event Horizon")).not.toHaveLength(0);
    expect(screen.getAllByText("CRX-0001-S01").length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("link", { name: /Open Workspace/i })[0],
    ).toHaveAttribute("href", "/projects/proj-1/scripts/sc-1");
  });

  it("shows loading empty and error states", async () => {
    listProjectScripts.mockReturnValue(new Promise(() => {}));
    const { unmount } = wrap(<ProjectScriptsPage />);
    expect(screen.getByTestId("scripts-loading")).toBeInTheDocument();
    unmount();

    listProjectScripts.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    });
    wrap(<ProjectScriptsPage />);
    expect(await screen.findByText("No scripts yet")).toBeInTheDocument();

    listProjectScripts.mockRejectedValue(new ApiError(500, "Backend down"));
    wrap(<ProjectScriptsPage />);
    expect(await screen.findByText("Backend down")).toBeInTheDocument();
  });

  it("supports search and status filtering", async () => {
    const user = userEvent.setup();
    listProjectScripts.mockResolvedValue({
      items: [scriptItem],
      page: 1,
      page_size: 20,
      total: 1,
    });
    wrap(<ProjectScriptsPage />);
    await screen.findAllByText("Event Horizon");
    await user.type(screen.getByLabelText("Search scripts"), "Horizon");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() =>
      expect(listProjectScripts).toHaveBeenCalledWith(
        expect.anything(),
        "proj-1",
        expect.objectContaining({ search: "Horizon" }),
      ),
    );
    await user.selectOptions(screen.getByLabelText("Filter by status"), "draft");
    await waitFor(() =>
      expect(listProjectScripts).toHaveBeenCalledWith(
        expect.anything(),
        "proj-1",
        expect.objectContaining({ status: "draft" }),
      ),
    );
  });

  it("navigates New Script flow to workspace", async () => {
    const user = userEvent.setup();
    listProjectScripts.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    });
    createScript.mockResolvedValue({
      ...scriptItem,
      id: "sc-new",
      title: "Fresh Script",
      documents: [],
    });
    wrap(<ProjectScriptsPage />);
    await screen.findByText("No scripts yet");
    await user.click(screen.getAllByRole("button", { name: "New Script" })[0]!);
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Title"), "Fresh Script");
    await user.click(within(dialog).getByRole("button", { name: /^Create Script$/ }));
    await waitFor(() =>
      expect(pushMock).toHaveBeenCalledWith("/projects/proj-1/scripts/sc-new"),
    );
  });
});
