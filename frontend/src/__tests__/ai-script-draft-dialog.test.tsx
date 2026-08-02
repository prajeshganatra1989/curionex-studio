import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GenerateScriptAiDraftDialog } from "@/components/scripts/generate-script-ai-draft-dialog";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiJob, AiModel, AiProvider, AiSettings } from "@/lib/ai/types";

const listProviders = vi.fn();
const listModels = vi.fn();
const getAiSettings = vi.fn();
const createScriptAiDraft = vi.fn();
const getScriptAiPrerequisites = vi.fn();
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
    getAiSettings: (...args: unknown[]) => getAiSettings(...args),
    createScriptAiDraft: (...args: unknown[]) => createScriptAiDraft(...args),
    getScriptAiPrerequisites: (...args: unknown[]) =>
      getScriptAiPrerequisites(...args),
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

const settings: AiSettings = {
  default_model_id: "model-1",
  default_temperature: 0.7,
  default_max_tokens: 2000,
  default_target_duration_seconds: 60,
  default_target_words_per_minute: 150,
};

function completedJob(overrides: Partial<AiJob> = {}): AiJob {
  return {
    id: "job-1",
    status: "completed",
    requested_by: "user-1",
    prompt_version_id: "ver-1",
    model_id: "model-1",
    input_variables: {},
    purpose: "script.discovery_brief.draft",
    script_id: "sc-1",
    document_type: "discovery_brief",
    project_id: "proj-1",
    generation_id: "gen-1",
    started_at: "2026-01-03T00:00:00Z",
    finished_at: "2026-01-03T00:00:05Z",
    duration_ms: 5000,
    retries: 0,
    error_message: null,
    created_at: "2026-01-03T00:00:00Z",
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

describe("GenerateScriptAiDraftDialog", () => {
  beforeEach(() => {
    listProviders.mockReset();
    listModels.mockReset();
    getAiSettings.mockReset();
    createScriptAiDraft.mockReset();
    getScriptAiPrerequisites.mockReset();
    getJob.mockReset();
    findGenerationIdForJob.mockReset();
    cancelJob.mockReset();

    listProviders.mockResolvedValue([provider]);
    listModels.mockResolvedValue([model]);
    getAiSettings.mockResolvedValue(settings);
    getScriptAiPrerequisites.mockResolvedValue({
      document_type: "discovery_brief",
      ready: true,
      missing: [],
    });
    getJob.mockResolvedValue(completedJob());
    findGenerationIdForJob.mockResolvedValue("gen-1");
  });

  it("shows human-review warning and form fields", async () => {
    wrap(
      <GenerateScriptAiDraftDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        documentType="discovery_brief"
        scriptTitle="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("script-ai-draft-form")).toBeInTheDocument();
    expect(
      screen.getByText(/AI-generated content is unverified/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Language")).toBeInTheDocument();
    expect(screen.getByLabelText("Tone")).toBeInTheDocument();
  });

  it("disables generate when prerequisites are missing", async () => {
    getScriptAiPrerequisites.mockResolvedValue({
      document_type: "story_spine",
      ready: false,
      missing: ["discovery_brief"],
    });

    wrap(
      <GenerateScriptAiDraftDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        documentType="story_spine"
        scriptTitle="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    expect(
      await screen.findByTestId("script-ai-prerequisites"),
    ).toHaveTextContent("Discovery Brief");
    expect(screen.getByTestId("script-ai-draft-submit")).toBeDisabled();
  });

  it("shows Save and Generate when dirty and saves before creating", async () => {
    createScriptAiDraft.mockResolvedValue(completedJob());
    const onSaveThenGenerate = vi.fn().mockResolvedValue(true);
    const onDraftReady = vi.fn();
    const user = userEvent.setup();

    wrap(
      <GenerateScriptAiDraftDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        documentType="discovery_brief"
        scriptTitle="Neutron Stars"
        isDirty
        onSaveThenGenerate={onSaveThenGenerate}
        onDraftReady={onDraftReady}
      />,
    );

    await screen.findByTestId("script-ai-draft-form");
    expect(screen.getByTestId("script-ai-dirty-hint")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save and Generate" }),
    ).toBeInTheDocument();

    await user.click(screen.getByTestId("script-ai-draft-submit"));

    await waitFor(() => expect(onSaveThenGenerate).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(createScriptAiDraft).toHaveBeenCalledTimes(1));
    const [, scriptId, documentType, payload] = createScriptAiDraft.mock.calls[0];
    expect(scriptId).toBe("sc-1");
    expect(documentType).toBe("discovery_brief");
    expect(payload.idempotency_key).toEqual(expect.any(String));
    await waitFor(() => expect(onDraftReady).toHaveBeenCalledWith("gen-1"));
  });

  it("shows wpm for master script and prevents duplicate submits", async () => {
    getScriptAiPrerequisites.mockResolvedValue({
      document_type: "master_script",
      ready: true,
      missing: [],
    });
    let resolveCreate: (job: AiJob) => void = () => {};
    createScriptAiDraft.mockImplementation(
      () =>
        new Promise<AiJob>((resolve) => {
          resolveCreate = resolve;
        }),
    );
    const user = userEvent.setup();

    wrap(
      <GenerateScriptAiDraftDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        documentType="master_script"
        scriptTitle="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    await screen.findByTestId("script-ai-draft-form");
    expect(screen.getByLabelText("Words per minute")).toBeInTheDocument();

    const button = screen.getByTestId("script-ai-draft-submit");
    await user.click(button);
    await user.click(button);
    await user.click(button);

    expect(createScriptAiDraft).toHaveBeenCalledTimes(1);
    resolveCreate(
      completedJob({
        purpose: "script.master_script.draft",
        document_type: "master_script",
      }),
    );
    await waitFor(() => expect(createScriptAiDraft).toHaveBeenCalledTimes(1));
  });

  it("toasts when draft creation fails", async () => {
    createScriptAiDraft.mockRejectedValue(
      new ApiError(422, "OpenAI provider is inactive."),
    );
    const user = userEvent.setup();

    wrap(
      <GenerateScriptAiDraftDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        documentType="discovery_brief"
        scriptTitle="Neutron Stars"
        onDraftReady={vi.fn()}
      />,
    );

    await screen.findByTestId("script-ai-draft-form");
    await user.click(screen.getByTestId("script-ai-draft-submit"));

    expect(
      await screen.findByText("Could not generate draft"),
    ).toBeInTheDocument();
  });
});
