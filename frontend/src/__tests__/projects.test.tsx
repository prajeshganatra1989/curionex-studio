import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectsPage } from "@/components/projects/projects-page";
import { ProjectHomePage } from "@/components/projects/project-home-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { Project } from "@/lib/api/types";

const replaceMock = vi.fn();
const pushMock = vi.fn();
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  usePathname: () => "/projects",
  useSearchParams: () => searchParams,
  useParams: () => ({ projectId: "proj-1" }),
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

const listProjects = vi.fn();
const getProject = vi.fn();
const createProject = vi.fn();
const updateProject = vi.fn();
const archiveProject = vi.fn();
const listCategories = vi.fn();
const createCategory = vi.fn();
const listTags = vi.fn();
const createTag = vi.fn();
const listProjectKnowledgePacks = vi.fn();
const listProjectScripts = vi.fn();
const createKnowledgePack = vi.fn();
const createScript = vi.fn();
const getLatestContentVersion = vi.fn();
const getApprovedContentVersion = vi.fn();
const getWorkflowStatus = vi.fn();

vi.mock("@/lib/api/projects", () => ({
  listProjects: (...args: unknown[]) => listProjects(...args),
  getProject: (...args: unknown[]) => getProject(...args),
  createProject: (...args: unknown[]) => createProject(...args),
  updateProject: (...args: unknown[]) => updateProject(...args),
  archiveProject: (...args: unknown[]) => archiveProject(...args),
  listCategories: (...args: unknown[]) => listCategories(...args),
  createCategory: (...args: unknown[]) => createCategory(...args),
  listTags: (...args: unknown[]) => listTags(...args),
  createTag: (...args: unknown[]) => createTag(...args),
  listProjectKnowledgePacks: (...args: unknown[]) =>
    listProjectKnowledgePacks(...args),
  listProjectScripts: (...args: unknown[]) => listProjectScripts(...args),
  createKnowledgePack: (...args: unknown[]) => createKnowledgePack(...args),
  createScript: (...args: unknown[]) => createScript(...args),
  getLatestContentVersion: (...args: unknown[]) =>
    getLatestContentVersion(...args),
  getApprovedContentVersion: (...args: unknown[]) =>
    getApprovedContentVersion(...args),
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

const sampleProject: Project = {
  id: "proj-1",
  project_code: "CRX-0001",
  name: "Black Holes Explained",
  description: "A deep dive into event horizons",
  status: "active",
  category_id: "cat-1",
  created_by: "u1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  category: {
    id: "cat-1",
    name: "Science",
    slug: "science",
    description: null,
    is_active: true,
    created_at: "",
    updated_at: "",
  },
  tags: [
    {
      id: "tag-1",
      name: "physics",
      slug: "physics",
      created_at: "",
      updated_at: "",
    },
  ],
};

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

describe("ProjectsPage", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    replaceMock.mockReset();
    pushMock.mockReset();
    listProjects.mockReset();
    createProject.mockReset();
    archiveProject.mockReset();
    listCategories.mockResolvedValue([
      {
        id: "cat-1",
        name: "Science",
        slug: "science",
        description: null,
        is_active: true,
        created_at: "",
        updated_at: "",
      },
    ]);
    listTags.mockResolvedValue([
      {
        id: "tag-1",
        name: "physics",
        slug: "physics",
        created_at: "",
        updated_at: "",
      },
      {
        id: "tag-2",
        name: "space",
        slug: "space",
        created_at: "",
        updated_at: "",
      },
    ]);
    createCategory.mockResolvedValue({
      id: "cat-2",
      name: "History",
      slug: "history",
      description: null,
      is_active: true,
      created_at: "",
      updated_at: "",
    });
    createTag.mockResolvedValue({
      id: "tag-3",
      name: "cosmos",
      slug: "cosmos",
      created_at: "",
      updated_at: "",
    });
  });

  it("renders projects page header", async () => {
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    expect(await screen.findByRole("heading", { name: "Projects" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /New Project/i })).toBeInTheDocument();
  });

  it("renders loading skeletons", () => {
    listProjects.mockReturnValue(new Promise(() => undefined));
    wrap(<ProjectsPage />);
    expect(document.querySelector("[aria-busy='true']")).toBeTruthy();
  });

  it("renders empty state", async () => {
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    wrap(<ProjectsPage />);
    expect(
      await screen.findByText("Create your first Curionex project"),
    ).toBeInTheDocument();
  });

  it("renders API error state", async () => {
    listProjects.mockRejectedValue(new ApiError(500, "Server exploded"));
    wrap(<ProjectsPage />);
    expect(await screen.findByText("Server exploded")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Try again/i })).toBeInTheDocument();
  });

  it("renders project cards", async () => {
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    expect(await screen.findByText("Black Holes Explained")).toBeInTheDocument();
    expect(screen.getByText("CRX-0001")).toBeInTheDocument();
    expect(screen.getAllByText("Science").length).toBeGreaterThan(0);
    expect(screen.getAllByText("physics").length).toBeGreaterThan(0);
  });

  it("paginates with next page query update", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 30,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.click(screen.getByRole("button", { name: "Next page" }));
    expect(replaceMock).toHaveBeenCalled();
    const url = String(replaceMock.mock.calls.at(-1)?.[0]);
    expect(url).toContain("page=2");
  });

  it("updates search query", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.type(
      screen.getByPlaceholderText(/Search by name or CRX code/i),
      "memory",
    );
    await waitFor(
      () => {
        expect(replaceMock).toHaveBeenCalled();
        expect(String(replaceMock.mock.calls.at(-1)?.[0])).toContain("search=memory");
      },
      { timeout: 2000 },
    );
  });

  it("applies status filter", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.selectOptions(screen.getByDisplayValue("All statuses"), "draft");
    expect(String(replaceMock.mock.calls.at(-1)?.[0])).toContain("status=draft");
  });

  it("applies category filter", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.selectOptions(screen.getByDisplayValue("All categories"), "cat-1");
    expect(String(replaceMock.mock.calls.at(-1)?.[0])).toContain("category_id=cat-1");
  });

  it("applies tag filter", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.selectOptions(screen.getByDisplayValue("All tags"), "tag-1");
    expect(String(replaceMock.mock.calls.at(-1)?.[0])).toContain("tag_id=tag-1");
  });

  it("resets filters", async () => {
    const user = userEvent.setup();
    searchParams = new URLSearchParams("status=draft&search=x");
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("No projects match these filters");
    await user.click(screen.getAllByRole("button", { name: "Reset filters" })[0]!);
    expect(replaceMock).toHaveBeenCalledWith("/projects");
  });

  it("opens create project modal", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create Project" })).toBeInTheDocument();
  });

  it("validates create form", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /^Create Project$/ }));
    expect(await within(dialog).findByText("Name is required")).toBeInTheDocument();
    expect(createProject).not.toHaveBeenCalled();
  });

  it("creates project and navigates home", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    createProject.mockResolvedValue({ ...sampleProject, id: "proj-new" });
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Name"), "Memory Palace");
    await user.click(within(dialog).getByRole("button", { name: /^Create Project$/ }));
    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ name: "Memory Palace" }),
      );
      expect(pushMock).toHaveBeenCalledWith("/projects/proj-new");
    });
  });

  it("prevents duplicate create submission", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    let resolveCreate: (value: Project) => void = () => undefined;
    createProject.mockImplementation(
      () =>
        new Promise<Project>((resolve) => {
          resolveCreate = resolve;
        }),
    );
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Name"), "Slow Project");
    const submit = within(dialog).getByRole("button", { name: /^Create Project$/ });
    await user.click(submit);
    expect(submit).toBeDisabled();
    resolveCreate({ ...sampleProject, id: "slow" });
    await waitFor(() => expect(pushMock).toHaveBeenCalled());
  });

  it("shows backend validation error on create", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    createProject.mockRejectedValue(new ApiError(422, "Name already exists"));
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Name"), "Dup");
    await user.click(within(dialog).getByRole("button", { name: /^Create Project$/ }));
    expect(await screen.findByText("Name already exists")).toBeInTheDocument();
  });

  it("loads categories and creates one", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByRole("button", { name: "Science" })).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText("Category"), "History");
    await user.click(within(dialog).getByRole("button", { name: /Create “History”/i }));
    await waitFor(() => expect(createCategory).toHaveBeenCalled());
  });

  it("loads tags, selects multiple, and creates a tag", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 12,
      total: 0,
    });
    wrap(<ProjectsPage />);
    await user.click(screen.getByRole("button", { name: /New Project/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(await within(dialog).findByRole("button", { name: "physics" }));
    await user.click(within(dialog).getByRole("button", { name: "space" }));
    expect(within(dialog).getByLabelText("Remove physics")).toBeInTheDocument();
    expect(within(dialog).getByLabelText("Remove space")).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText("Tags"), "cosmos");
    await user.click(within(dialog).getByRole("button", { name: /Create “cosmos”/i }));
    await waitFor(() => expect(createTag).toHaveBeenCalled());
  });

  it("shows archive confirmation and archives", async () => {
    const user = userEvent.setup();
    listProjects.mockResolvedValue({
      items: [sampleProject],
      page: 1,
      page_size: 12,
      total: 1,
    });
    archiveProject.mockResolvedValue({ ...sampleProject, status: "archived" });
    wrap(<ProjectsPage />);
    await screen.findByText("Black Holes Explained");
    await user.click(
      screen.getByRole("button", { name: /Actions for Black Holes Explained/i }),
    );
    await user.click(screen.getByRole("menuitem", { name: "Archive" }));
    expect(await screen.findByText("Archive project?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Archive project" }));
    await waitFor(() =>
      expect(archiveProject).toHaveBeenCalledWith(expect.anything(), "proj-1"),
    );
  });
});

describe("ProjectHomePage", () => {
  beforeEach(() => {
    getProject.mockReset();
    updateProject.mockReset();
    archiveProject.mockReset();
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
      page_size: 5,
      total: 1,
    });
    listProjectScripts.mockResolvedValue({
      items: [
        {
          id: "sc-1",
          project_id: "proj-1",
          knowledge_pack_id: "kp-1",
          script_code: "SCR-0001",
          title: "Event Horizon",
          description: null,
          status: "draft",
          content_version_id: null,
          created_by: "u1",
          created_at: "",
          updated_at: "",
        },
      ],
      page: 1,
      page_size: 5,
      total: 1,
    });
    getLatestContentVersion.mockResolvedValue({
      id: "v1",
      project_id: "proj-1",
      version_number: 2,
      status: "draft",
      title: "Latest",
      content: "",
      created_by: "u1",
      created_at: "",
    });
    getApprovedContentVersion.mockResolvedValue(null);
    getWorkflowStatus.mockResolvedValue({
      script_id: "sc-1",
      stage: "discovery_brief",
      status: "in_progress",
      active_version: { id: "v1", version_number: 2, status: "draft", title: "Latest" },
      latest_version: { id: "v1", version_number: 2, status: "draft", title: "Latest" },
      approved_version: null,
      pending_approval: null,
    });
    listCategories.mockResolvedValue([sampleProject.category]);
    listTags.mockResolvedValue(sampleProject.tags);
    createKnowledgePack.mockResolvedValue({
      id: "kp-2",
      project_id: "proj-1",
      name: "New Pack",
      description: null,
      status: "draft",
      created_by: "u1",
      created_at: "",
      updated_at: "",
    });
    createScript.mockResolvedValue({
      id: "sc-2",
      project_id: "proj-1",
      knowledge_pack_id: null,
      script_code: "SCR-0002",
      title: "New Script",
      description: null,
      status: "draft",
      content_version_id: null,
      created_by: "u1",
      created_at: "",
      updated_at: "",
    });
  });

  it("renders project home header and panels", async () => {
    getProject.mockResolvedValue(sampleProject);
    wrap(<ProjectHomePage />);
    expect(await screen.findByRole("heading", { name: "Black Holes Explained" })).toBeInTheDocument();
    expect(screen.getByText("CRX-0001")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Knowledge Packs" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Scripts" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Workflow" })).toBeInTheDocument();
    expect(screen.getByText("Core Facts")).toBeInTheDocument();
    expect(screen.getByText("Event Horizon")).toBeInTheDocument();
  });

  it("renders restricted activity state", async () => {
    getProject.mockResolvedValue(sampleProject);
    wrap(<ProjectHomePage />);
    expect(await screen.findByText("Activity unavailable")).toBeInTheDocument();
  });

  it("renders not-found state", async () => {
    getProject.mockRejectedValue(new ApiError(404, "Not found"));
    wrap(<ProjectHomePage />);
    expect(await screen.findByText("Project not found")).toBeInTheDocument();
  });

  it("edits project without changing code", async () => {
    const user = userEvent.setup();
    getProject.mockResolvedValue(sampleProject);
    updateProject.mockResolvedValue({ ...sampleProject, name: "Updated" });
    wrap(<ProjectHomePage />);
    await screen.findByRole("heading", { name: "Black Holes Explained" });
    await user.click(screen.getByRole("button", { name: /Edit/i }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("CRX-0001")).toBeInTheDocument();
    expect(within(dialog).queryByLabelText(/project code/i)).not.toBeInTheDocument();
    await user.clear(within(dialog).getByLabelText("Name"));
    await user.type(within(dialog).getByLabelText("Name"), "Updated Title");
    await user.click(within(dialog).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(updateProject).toHaveBeenCalledWith(
        expect.anything(),
        "proj-1",
        expect.objectContaining({ name: "Updated Title" }),
      ),
    );
  });

  it("creates knowledge pack", async () => {
    const user = userEvent.setup();
    getProject.mockResolvedValue(sampleProject);
    wrap(<ProjectHomePage />);
    await screen.findByRole("heading", { name: "Black Holes Explained" });
    await user.click(screen.getByRole("button", { name: "Create Knowledge Pack" }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Name"), "Research Pack");
    await user.click(
      within(dialog).getByRole("button", { name: /^Create Knowledge Pack$/ }),
    );
    await waitFor(() =>
      expect(createKnowledgePack).toHaveBeenCalledWith(
        expect.anything(),
        "proj-1",
        expect.objectContaining({ name: "Research Pack" }),
      ),
    );
  });

  it("creates script with project knowledge pack only", async () => {
    const user = userEvent.setup();
    getProject.mockResolvedValue(sampleProject);
    wrap(<ProjectHomePage />);
    await screen.findByRole("heading", { name: "Black Holes Explained" });
    await user.click(screen.getByRole("button", { name: "Create Script" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("option", { name: "Core Facts" })).toBeInTheDocument();
    expect(within(dialog).queryByRole("option", { name: /Other Project/i })).not.toBeInTheDocument();
    await user.type(within(dialog).getByLabelText("Title"), "New Script");
    await user.selectOptions(within(dialog).getByLabelText("Knowledge Pack"), "kp-1");
    await user.click(within(dialog).getByRole("button", { name: /^Create Script$/ }));
    await waitFor(() =>
      expect(createScript).toHaveBeenCalledWith(
        expect.anything(),
        "proj-1",
        expect.objectContaining({
          title: "New Script",
          knowledge_pack_id: "kp-1",
        }),
      ),
    );
  });
});
