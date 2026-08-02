import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PromptEditorPage } from "@/components/ai/prompt-editor-page";
import { PromptsPage } from "@/components/ai/prompts-page";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type {
  AiPrompt,
  PaginatedResponse,
  AiPromptVersion,
} from "@/lib/ai/types";

const pushMock = vi.fn();
const replaceMock = vi.fn();
const listPrompts = vi.fn();
const getPrompt = vi.fn();
const listPromptVersions = vi.fn();
const createPrompt = vi.fn();
const updatePrompt = vi.fn();
const createPromptVersion = vi.fn();
const activatePromptVersion = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/ai/prompts",
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

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    listPrompts: (...args: unknown[]) => listPrompts(...args),
    getPrompt: (...args: unknown[]) => getPrompt(...args),
    listPromptVersions: (...args: unknown[]) => listPromptVersions(...args),
    createPrompt: (...args: unknown[]) => createPrompt(...args),
    updatePrompt: (...args: unknown[]) => updatePrompt(...args),
    createPromptVersion: (...args: unknown[]) => createPromptVersion(...args),
    activatePromptVersion: (...args: unknown[]) =>
      activatePromptVersion(...args),
  };
});

vi.mock("@/lib/api/content-standards", () => ({
  getContentStandardSummary: vi.fn().mockResolvedValue({
    id: "std-1",
    name: "Curionex Content Standard",
    version: "1",
    status: "active",
    label: "Curionex Content Standard v1",
    updated_at: "2026-08-01T00:00:00Z",
    has_active: true,
  }),
  getActiveContentStandard: vi.fn(),
  listContentStandards: vi.fn(),
  getContentStandard: vi.fn(),
}));

vi.mock("@/lib/auth/auth-context", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "user-1",
      email: "user@example.com",
      first_name: "Test",
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

const version: AiPromptVersion = {
  id: "ver-1",
  prompt_id: "prompt-1",
  version_number: 1,
  system_prompt: "You are helpful.",
  user_template: "Write about {{topic}}.",
  variables: ["topic"],
  status: "active",
  created_by: "user-1",
  created_at: "2026-01-03T00:00:00Z",
};

const prompt: AiPrompt = {
  id: "prompt-1",
  name: "Discovery brief",
  description: "Generates briefs",
  purpose: "scripting",
  status: "active",
  owner_id: "user-1",
  active_version_id: "ver-1",
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  active_version: version,
};

const listResponse: PaginatedResponse<AiPrompt> = {
  items: [prompt],
  page: 1,
  page_size: 12,
  total: 1,
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

describe("AI Prompts UI", () => {
  beforeEach(() => {
    listPrompts.mockReset();
    getPrompt.mockReset();
    listPromptVersions.mockReset();
    createPrompt.mockReset();
    updatePrompt.mockReset();
    createPromptVersion.mockReset();
    activatePromptVersion.mockReset();
    listPrompts.mockResolvedValue(listResponse);
    getPrompt.mockResolvedValue(prompt);
    listPromptVersions.mockResolvedValue([version]);
  });

  it("lists prompts", async () => {
    wrap(<PromptsPage />);
    expect(await screen.findByTestId("prompts-list")).toBeInTheDocument();
    expect(screen.getByText("Discovery brief")).toBeInTheDocument();
  });

  it("shows restricted state on 403", async () => {
    listPrompts.mockRejectedValue(new ApiError(403, "Forbidden"));
    wrap(<PromptsPage />);
    expect(await screen.findByText("Access restricted")).toBeInTheDocument();
  });

  it("renders prompt editor with templates and version history", async () => {
    wrap(<PromptEditorPage promptId="prompt-1" />);
    expect(await screen.findByTestId("prompt-editor")).toBeInTheDocument();
    expect(screen.getByDisplayValue("You are helpful.")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Write about {{topic}}.")).toBeInTheDocument();
    expect(screen.getByTestId("version-history")).toHaveTextContent("v1");
    expect(screen.getByTestId("variable-chips")).toHaveTextContent("{{topic}}");
    expect(await screen.findByTestId("content-standard-usage")).toHaveTextContent(
      "Uses: Curionex Content Standard v1",
    );
  });

  it("validates variables before saving a new version", async () => {
    const user = userEvent.setup();
    wrap(<PromptEditorPage promptId="prompt-1" />);
    await screen.findByTestId("prompt-editor");
    const userTemplate = screen.getByLabelText("User template");
    await user.clear(userTemplate);
    await user.type(userTemplate, "Hello without placeholders");
    expect(
      screen.getByRole("button", { name: "Save as new version" }),
    ).toBeDisabled();
  });
});
