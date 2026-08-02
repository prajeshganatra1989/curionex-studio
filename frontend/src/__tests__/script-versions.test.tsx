import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScriptVersionPage } from "@/components/scripts/script-version-page";
import { ToastProvider } from "@/components/ui/toast";
import type { ScriptDetail } from "@/lib/api/types";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";

const getScript = vi.fn();
const getContentVersion = vi.fn();

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/lib/api/projects", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/projects")>(
    "@/lib/api/projects",
  );
  return {
    ...actual,
    getScript: (...args: unknown[]) => getScript(...args),
    getContentVersion: (...args: unknown[]) => getContentVersion(...args),
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

function makeScript(): ScriptDetail {
  return {
    id: "sc-1",
    project_id: "proj-1",
    knowledge_pack_id: null,
    script_code: "CRX-0042-S01",
    title: "Neutron Stars",
    description: null,
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
      content: "",
      position: index + 1,
      created_at: "",
      updated_at: "",
    })),
  };
}

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

describe("ScriptVersionPage", () => {
  beforeEach(() => {
    getScript.mockReset();
    getContentVersion.mockReset();
    getScript.mockResolvedValue(makeScript());
    getContentVersion.mockResolvedValue({
      id: "v1",
      project_id: "proj-1",
      script_id: "sc-1",
      version_number: 2,
      status: "draft",
      title: "CRX-0042-S01 — Neutron Stars",
      content: [
        "DISCOVERY BRIEF",
        "",
        "Brief snapshot",
        "",
        "STORY SPINE",
        "",
        "Spine snapshot",
        "",
        "MASTER SCRIPT",
        "",
        "Script snapshot",
        "",
      ].join("\n"),
      created_by: "u1",
      created_at: "2026-01-03T00:00:00Z",
    });
  });

  it("renders parsed snapshot sections", async () => {
    wrap(
      <ScriptVersionPage
        projectId="proj-1"
        scriptId="sc-1"
        versionId="v1"
      />,
    );
    expect(await screen.findByRole("heading", { name: "Version 2" })).toBeInTheDocument();
    expect(screen.getByTestId("version-section-discovery_brief")).toHaveTextContent(
      "Brief snapshot",
    );
    expect(screen.getByTestId("version-section-story_spine")).toHaveTextContent(
      "Spine snapshot",
    );
    expect(screen.getByTestId("version-section-master_script")).toHaveTextContent(
      "Script snapshot",
    );
  });

  it("links back to workspace", async () => {
    wrap(
      <ScriptVersionPage
        projectId="proj-1"
        scriptId="sc-1"
        versionId="v1"
      />,
    );
    expect(await screen.findByRole("link", { name: /Back to Workspace/i })).toHaveAttribute(
      "href",
      "/projects/proj-1/scripts/sc-1",
    );
  });
});
