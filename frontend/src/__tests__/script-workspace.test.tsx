import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScriptWorkspace } from "@/components/scripts/script-workspace";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type {
  KnowledgePackDetail,
  Project,
  ScriptDetail,
  WorkflowStatus,
} from "@/lib/api/types";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import { SECTION_ORDER } from "@/lib/knowledge-packs/sections";

const pushMock = vi.fn();
const getScript = vi.fn();
const getProject = vi.fn();
const getWorkflowStatus = vi.fn();
const getScriptWorkflow = vi.fn();
const updateScriptDocument = vi.fn();
const updateScript = vi.fn();
const createWorkflowVersion = vi.fn();
const submitWorkflowReview = vi.fn();
const getKnowledgePack = vi.fn();
const listProjectKnowledgePacks = vi.fn();
const listScriptContentVersions = vi.fn();
const getApprovalDetail = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ projectId: "proj-1", scriptId: "sc-1" }),
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
    getScript: (...args: unknown[]) => getScript(...args),
    getProject: (...args: unknown[]) => getProject(...args),
    getWorkflowStatus: (...args: unknown[]) => getWorkflowStatus(...args),
    getScriptWorkflow: (...args: unknown[]) => getScriptWorkflow(...args),
    updateScriptDocument: (...args: unknown[]) => updateScriptDocument(...args),
    updateScript: (...args: unknown[]) => updateScript(...args),
    createWorkflowVersion: (...args: unknown[]) => createWorkflowVersion(...args),
    submitWorkflowReview: (...args: unknown[]) => submitWorkflowReview(...args),
    getKnowledgePack: (...args: unknown[]) => getKnowledgePack(...args),
    listProjectKnowledgePacks: (...args: unknown[]) =>
      listProjectKnowledgePacks(...args),
  };
});

vi.mock("@/lib/api/approvals", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/approvals")>(
    "@/lib/api/approvals",
  );
  return {
    ...actual,
    listScriptContentVersions: (...args: unknown[]) =>
      listScriptContentVersions(...args),
    getApprovalDetail: (...args: unknown[]) => getApprovalDetail(...args),
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
  project_code: "CRX-0042",
  name: "Cosmic Mysteries",
  description: null,
  status: "active",
  category_id: null,
  created_by: "u1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  category: null,
  tags: [],
};

function makeScript(overrides: Partial<ScriptDetail> = {}): ScriptDetail {
  return {
    id: "sc-1",
    project_id: "proj-1",
    knowledge_pack_id: "kp-1",
    script_code: "CRX-0042-S01",
    title: "Neutron Stars",
    description: "Short about neutron stars",
    status: "draft",
    content_version_id: null,
    created_by: "u1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    documents: DOCUMENT_ORDER.map((meta, index) => ({
      id: `doc-${meta.type}`,
      script_id: "sc-1",
      document_type: meta.type,
      title: meta.title,
      content:
        meta.type === "discovery_brief"
          ? "Initial discovery brief content for loading"
          : "",
      position: index + 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    })),
    ...overrides,
  };
}

function makeWorkflow(overrides: Partial<WorkflowStatus> = {}): WorkflowStatus {
  return {
    script_id: "sc-1",
    stage: "workspace",
    status: "active",
    active_version: null,
    latest_version: null,
    approved_version: null,
    pending_approval: null,
    ...overrides,
  };
}

function makePack(): KnowledgePackDetail {
  return {
    id: "kp-1",
    project_id: "proj-1",
    name: "Star Research",
    description: null,
    status: "draft",
    created_by: "u1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    sections: SECTION_ORDER.map((meta, index) => ({
      id: `sec-${meta.key}`,
      knowledge_pack_id: "kp-1",
      section_key: meta.key,
      title: meta.title,
      content: meta.key === "research" ? "Dense research notes" : "",
      position: index + 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    })),
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

describe("ScriptWorkspace", () => {
  beforeEach(() => {
    pushMock.mockReset();
    getScript.mockReset();
    getProject.mockReset();
    getWorkflowStatus.mockReset();
    getScriptWorkflow.mockReset();
    updateScriptDocument.mockReset();
    updateScript.mockReset();
    createWorkflowVersion.mockReset();
    submitWorkflowReview.mockReset();
    getKnowledgePack.mockReset();
    listProjectKnowledgePacks.mockReset();
    listScriptContentVersions.mockReset();
    getApprovalDetail.mockReset();

    getProject.mockResolvedValue(project);
    getScript.mockResolvedValue(makeScript());
    getWorkflowStatus.mockResolvedValue(makeWorkflow());
    getScriptWorkflow.mockResolvedValue({
      id: "wf-1",
      script_id: "sc-1",
      current_stage: "workspace",
      status: "active",
      active_content_version_id: null,
      created_at: "",
      updated_at: "",
      script: null,
      knowledge_pack_id: "kp-1",
      active_content_version: null,
      latest_approval: null,
    });
    getKnowledgePack.mockResolvedValue(makePack());
    listProjectKnowledgePacks.mockResolvedValue({
      items: [
        {
          id: "kp-1",
          project_id: "proj-1",
          name: "Star Research",
          description: null,
          status: "draft",
          created_by: "u1",
          created_at: "",
          updated_at: "",
        },
      ],
      page: 1,
      page_size: 50,
      total: 1,
    });
    listScriptContentVersions.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
    });
    getApprovalDetail.mockResolvedValue({
      id: "ap-1",
      status: "rejected",
      comment: "Rewrite the ending",
      created_at: "",
      reviewed_at: "",
      requested_by: {
        id: "u1",
        email: "owner@example.com",
        first_name: "Owner",
        last_name: "User",
      },
      reviewed_by: null,
      content_version: {
        id: "v1",
        project_id: "proj-1",
        script_id: "sc-1",
        version_number: 1,
        status: "rejected",
        title: "v1",
        content: "",
        created_by: "u1",
        created_at: "",
      },
      project: {
        id: "proj-1",
        project_code: "CRX-0042",
        name: "Cosmic Mysteries",
      },
      script: {
        id: "sc-1",
        script_code: "CRX-0042-S01",
        title: "Neutron Stars",
        project_id: "proj-1",
        knowledge_pack_id: "kp-1",
      },
      version_approvals: [],
    });
    class IO {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("IntersectionObserver", IO);
  });

  it("renders workspace header and three documents", async () => {
    wrap(<ScriptWorkspace />);
    expect(
      await screen.findByRole("heading", { name: "Neutron Stars" }),
    ).toBeInTheDocument();
    expect(screen.getByText("CRX-0042")).toBeInTheDocument();
    expect(screen.getByText("CRX-0042-S01")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to Project/i })).toBeInTheDocument();
    for (const meta of DOCUMENT_ORDER) {
      expect(
        screen.getByRole("heading", { name: meta.title, level: 2 }),
      ).toBeInTheDocument();
    }
    expect(
      screen.getByDisplayValue("Initial discovery brief content for loading"),
    ).toBeInTheDocument();
  });

  it("shows empty document guidance and preserves edits across documents", async () => {
    const user = userEvent.setup();
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    const master = screen.getByTestId("editor-master_script");
    expect(master).toHaveAttribute(
      "placeholder",
      expect.stringContaining("spoken narration"),
    );
    await user.type(master, "Spoken line one");
    await user.click(screen.getByTestId("doc-nav-story_spine"));
    expect(screen.getByTestId("editor-master_script")).toHaveValue("Spoken line one");
    expect(screen.getByTestId("save-status")).toHaveTextContent("Unsaved changes");
  });

  it("saves only changed documents and clears dirty state", async () => {
    const user = userEvent.setup();
    updateScriptDocument.mockImplementation(
      async (_api: unknown, _id: string, type: string, payload: { content: string }) => ({
        id: `doc-${type}`,
        script_id: "sc-1",
        document_type: type,
        title: type,
        content: payload.content,
        position: 1,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-03T00:00:00Z",
      }),
    );
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    await user.type(screen.getByTestId("editor-story_spine"), "Hook then twist");
    await user.click(screen.getByRole("button", { name: /Save Changes/i }));
    await waitFor(() => expect(updateScriptDocument).toHaveBeenCalledTimes(1));
    expect(updateScriptDocument).toHaveBeenCalledWith(
      expect.anything(),
      "sc-1",
      "story_spine",
      { content: "Hook then twist" },
    );
    await waitFor(() =>
      expect(screen.getByTestId("save-status")).not.toHaveTextContent(
        "Unsaved changes",
      ),
    );
  });

  it("preserves content on failed save and supports retry", async () => {
    const user = userEvent.setup();
    updateScriptDocument
      .mockRejectedValueOnce(new ApiError(500, "Save unavailable"))
      .mockResolvedValueOnce({
        id: "doc-story_spine",
        script_id: "sc-1",
        document_type: "story_spine",
        title: "Story Spine",
        content: "Retried content",
        position: 2,
        created_at: "",
        updated_at: "2026-01-03T00:00:00Z",
      });
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    const editor = screen.getByTestId("editor-story_spine");
    await user.clear(editor);
    await user.type(editor, "Retried content");
    await user.click(screen.getByRole("button", { name: /Save Changes/i }));
    expect(
      await screen.findByText(/Save failed: Save unavailable/i),
    ).toBeInTheDocument();
    expect(editor).toHaveValue("Retried content");
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(updateScriptDocument).toHaveBeenCalledTimes(2));
  });

  it("loads associated Knowledge Pack context without copying into documents", async () => {
    wrap(<ScriptWorkspace />);
    await screen.findByTestId("kp-context-panel");
    expect(screen.getByText("Star Research")).toBeInTheDocument();
    expect(screen.getByText("Dense research notes")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open Knowledge Pack/i })).toHaveAttribute(
      "href",
      "/projects/proj-1/knowledge-packs/kp-1",
    );
    expect(screen.getByTestId("editor-discovery_brief")).not.toHaveValue(
      "Dense research notes",
    );
  });

  it("shows no-pack state", async () => {
    getScript.mockResolvedValue(makeScript({ knowledge_pack_id: null }));
    wrap(<ScriptWorkspace />);
    expect(await screen.findByTestId("kp-context-empty")).toBeInTheDocument();
    expect(screen.getByText(/No Knowledge Pack linked/i)).toBeInTheDocument();
  });

  it("updates title and keeps script code read-only", async () => {
    const user = userEvent.setup();
    updateScript.mockResolvedValue(
      makeScript({ title: "Updated Stars" }),
    );
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    await user.click(screen.getByRole("button", { name: /Edit details/i }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByLabelText("Script code")).toHaveAttribute(
      "readOnly",
    );
    const titleInput = within(dialog).getByLabelText("Title");
    fireEvent.change(titleInput, { target: { value: "Updated Stars" } });
    await user.click(within(dialog).getByRole("button", { name: /Save details/i }));
    await waitFor(() => expect(updateScript).toHaveBeenCalled());
    expect(updateScript.mock.calls[0]?.[2]).toEqual(
      expect.objectContaining({ title: "Updated Stars" }),
    );
  });

  it("creates a version from the confirmation dialog", async () => {
    const user = userEvent.setup();
    getScript.mockResolvedValue(
      makeScript({
        documents: DOCUMENT_ORDER.map((meta, index) => ({
          id: `doc-${meta.type}`,
          script_id: "sc-1",
          document_type: meta.type,
          title: meta.title,
          content: "x".repeat(meta.completeMinChars),
          position: index + 1,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-02T00:00:00Z",
        })),
      }),
    );
    createWorkflowVersion.mockResolvedValue({
      workflow: {
        id: "wf-1",
        script_id: "sc-1",
        current_stage: "versioning",
        status: "active",
        active_content_version_id: "v1",
        created_at: "",
        updated_at: "",
        script: null,
        knowledge_pack_id: "kp-1",
        active_content_version: {
          id: "v1",
          version_number: 1,
          status: "draft",
          title: "CRX-0042-S01 — Neutron Stars",
          created_at: "",
        },
        latest_approval: null,
      },
      content_version: {
        id: "v1",
        version_number: 1,
        status: "draft",
        title: "CRX-0042-S01 — Neutron Stars",
        created_at: "",
      },
    });
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    const createButtons = screen.getAllByRole("button", {
      name: /^Create Version$/i,
    });
    await user.click(createButtons[0]!);
    const dialog = await screen.findByRole("dialog");
    await user.click(
      within(dialog).getByRole("button", { name: /^Create Version$/i }),
    );
    await waitFor(() => expect(createWorkflowVersion).toHaveBeenCalled());
  });

  it("renders pending review and approved states", async () => {
    getWorkflowStatus.mockResolvedValue(
      makeWorkflow({
        stage: "review",
        pending_approval: {
          id: "ap-1",
          status: "pending",
          content_version_id: "v1",
          created_at: "",
          reviewed_at: null,
        },
      }),
    );
    const { unmount } = wrap(<ScriptWorkspace />);
    expect(await screen.findByTestId("pending-review-banner")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-action")).toHaveAttribute(
      "data-action",
      "view_review",
    );
    unmount();

    getWorkflowStatus.mockResolvedValue(
      makeWorkflow({
        stage: "completed",
        status: "completed",
        approved_version: {
          id: "v1",
          version_number: 1,
          status: "approved",
          title: "Approved",
        },
      }),
    );
    wrap(<ScriptWorkspace />);
    expect(await screen.findByTestId("approved-banner")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-action")).toHaveAttribute(
      "data-action",
      "approved",
    );
  });

  it("renders rejected revision state", async () => {
    getWorkflowStatus.mockResolvedValue(makeWorkflow({ stage: "workspace" }));
    getScriptWorkflow.mockResolvedValue({
      id: "wf-1",
      script_id: "sc-1",
      current_stage: "workspace",
      status: "active",
      active_content_version_id: "v1",
      created_at: "",
      updated_at: "",
      script: null,
      knowledge_pack_id: "kp-1",
      active_content_version: null,
      latest_approval: {
        id: "ap-1",
        status: "rejected",
        content_version_id: "v1",
        created_at: "",
        reviewed_at: "",
      },
    });
    wrap(<ScriptWorkspace />);
    expect(await screen.findByTestId("revisions-banner")).toBeInTheDocument();
    expect(await screen.findByTestId("rejection-comment")).toHaveTextContent(
      "Rewrite the ending",
    );
    expect(screen.getByTestId("workflow-action")).toHaveAttribute(
      "data-action",
      "revisions_requested",
    );
  });

  it("shows 404 and 403 states", async () => {
    getScript.mockRejectedValue(new ApiError(404, "Missing"));
    const { unmount } = wrap(<ScriptWorkspace />);
    expect(await screen.findByText("Script not found")).toBeInTheDocument();
    unmount();

    getScript.mockRejectedValue(new ApiError(403, "Forbidden"));
    wrap(<ScriptWorkspace />);
    expect(await screen.findByText("Access restricted")).toBeInTheDocument();
  });

  it("triggers save with Cmd/Ctrl+S", async () => {
    const user = userEvent.setup();
    updateScriptDocument.mockResolvedValue({
      id: "doc-story_spine",
      script_id: "sc-1",
      document_type: "story_spine",
      title: "Story Spine",
      content: "Saved via shortcut",
      position: 2,
      created_at: "",
      updated_at: "2026-01-03T00:00:00Z",
    });
    wrap(<ScriptWorkspace />);
    await screen.findByRole("heading", { name: "Neutron Stars" });
    await user.type(screen.getByTestId("editor-story_spine"), "Saved via shortcut");
    await user.keyboard("{Control>}s{/Control}");
    await waitFor(() => expect(updateScriptDocument).toHaveBeenCalled());
  });
});
