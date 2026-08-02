import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GenerateAiDraftDialog } from "@/components/knowledge-packs/generate-ai-draft-dialog";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiJob, AiModel, AiProvider } from "@/lib/ai/types";

const listProviders = vi.fn();
const listModels = vi.fn();
const createKnowledgePackAiDraft = vi.fn();
const getJob = vi.fn();
const findGenerationIdForJob = vi.fn();
const cancelJob = vi.fn();

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    listProviders: (...args: unknown[]) => listProviders(...args),
    listModels: (...args: unknown[]) => listModels(...args),
    createKnowledgePackAiDraft: (...args: unknown[]) =>
      createKnowledgePackAiDraft(...args),
    getJob: (...args: unknown[]) => getJob(...args),
    findGenerationIdForJob: (...args: unknown[]) =>
      findGenerationIdForJob(...args),
    cancelJob: (...args: unknown[]) => cancelJob(...args),
  };
});

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

const provider: AiProvider = {
  id: "prov-openai",
  code: "openai",
  name: "OpenAI",
  is_active: true,
  base_url: null,
  has_credentials: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const model: AiModel = {
  id: "model-1",
  provider_id: "prov-openai",
  code: "gpt-4o",
  name: "GPT-4o",
  context_window: 128000,
  supports_reasoning: false,
  supports_streaming: true,
  is_active: true,
  is_default: true,
  pricing_input_per_1k: 0.005,
  pricing_output_per_1k: 0.015,
};

function completedJob(): AiJob {
  return {
    id: "job-1",
    status: "completed",
    requested_by: "user-1",
    prompt_version_id: "ver-1",
    model_id: "model-1",
    input_variables: { topic: "Neutron stars" },
    purpose: "knowledge_pack.draft",
    knowledge_pack_id: "kp-1",
    project_id: "proj-1",
    started_at: "2026-01-03T00:00:00Z",
    finished_at: "2026-01-03T00:00:05Z",
    duration_ms: 5000,
    retries: 0,
    error_message: null,
    created_at: "2026-01-03T00:00:00Z",
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

describe("GenerateAiDraftDialog", () => {
  beforeEach(() => {
    listProviders.mockReset();
    listModels.mockReset();
    createKnowledgePackAiDraft.mockReset();
    getJob.mockReset();
    findGenerationIdForJob.mockReset();
    cancelJob.mockReset();

    listProviders.mockResolvedValue([provider]);
    listModels.mockResolvedValue([model]);
    getJob.mockResolvedValue(completedJob());
    findGenerationIdForJob.mockResolvedValue("gen-1");
  });

  it("shows the unverified content warning and the draft form", async () => {
    wrap(
      <GenerateAiDraftDialog
        open
        onClose={vi.fn()}
        projectId="proj-1"
        knowledgePackId="kp-1"
        packName="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("ai-draft-form")).toBeInTheDocument();
    expect(screen.getByText(/AI-generated content is unverified/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate Draft" }),
    ).toBeInTheDocument();
  });

  it("creates a draft with an idempotency key and reports the generation once ready", async () => {
    createKnowledgePackAiDraft.mockResolvedValue(completedJob());
    const onDraftReady = vi.fn();
    const user = userEvent.setup();

    wrap(
      <GenerateAiDraftDialog
        open
        onClose={vi.fn()}
        projectId="proj-1"
        knowledgePackId="kp-1"
        packName="Neutron Stars"
        onDraftReady={onDraftReady}
      />,
    );

    await screen.findByTestId("ai-draft-form");
    await user.click(screen.getByRole("button", { name: "Generate Draft" }));

    await waitFor(() => expect(createKnowledgePackAiDraft).toHaveBeenCalledTimes(1));
    const [, projectId, knowledgePackId, payload] =
      createKnowledgePackAiDraft.mock.calls[0];
    expect(projectId).toBe("proj-1");
    expect(knowledgePackId).toBe("kp-1");
    expect(typeof payload.idempotency_key).toBe("string");
    expect(payload.idempotency_key.length).toBeGreaterThan(0);
    expect(payload.target_audience).toBe("general learners");

    await waitFor(() => expect(onDraftReady).toHaveBeenCalledWith("gen-1"));
  });

  it("prevents duplicate submissions while a draft is being created", async () => {
    let resolveCreate: (job: AiJob) => void = () => {};
    createKnowledgePackAiDraft.mockImplementation(
      () =>
        new Promise<AiJob>((resolve) => {
          resolveCreate = resolve;
        }),
    );
    const user = userEvent.setup();

    wrap(
      <GenerateAiDraftDialog
        open
        onClose={vi.fn()}
        projectId="proj-1"
        knowledgePackId="kp-1"
        packName="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    await screen.findByTestId("ai-draft-form");
    const button = screen.getByTestId("ai-draft-submit");
    await user.click(button);
    await user.click(button);
    await user.click(button);

    expect(createKnowledgePackAiDraft).toHaveBeenCalledTimes(1);
    const firstKey = createKnowledgePackAiDraft.mock.calls[0][3].idempotency_key;

    resolveCreate(completedJob());
    await waitFor(() => expect(findGenerationIdForJob).toHaveBeenCalled());
    expect(createKnowledgePackAiDraft).toHaveBeenCalledTimes(1);
    expect(firstKey).toEqual(expect.any(String));
  });

  it("shows an error toast when draft creation fails", async () => {
    createKnowledgePackAiDraft.mockRejectedValue(
      new ApiError(422, "OpenAI provider is inactive."),
    );
    const user = userEvent.setup();

    wrap(
      <GenerateAiDraftDialog
        open
        onClose={vi.fn()}
        projectId="proj-1"
        knowledgePackId="kp-1"
        packName="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    await screen.findByTestId("ai-draft-form");
    await user.click(screen.getByRole("button", { name: "Generate Draft" }));

    expect(
      await screen.findByText("Could not generate draft"),
    ).toBeInTheDocument();
    expect(screen.getByText("OpenAI provider is inactive.")).toBeInTheDocument();
  });
});
