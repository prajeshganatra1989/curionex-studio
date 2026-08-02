import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewScriptQualityDialog } from "@/components/scripts/review-script-quality-dialog";
import { ToastProvider } from "@/components/ui/toast";
import type { AiJob, AiModel, AiProvider, AiSettings } from "@/lib/ai/types";

const listProviders = vi.fn();
const listModels = vi.fn();
const getAiSettings = vi.fn();
const createScriptQualityReview = vi.fn();
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
    createScriptQualityReview: (...args: unknown[]) =>
      createScriptQualityReview(...args),
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
    purpose: "script.quality_review",
    script_id: "sc-1",
    document_type: "master_script",
    project_id: "proj-1",
    generation_id: "gen-qr-1",
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

describe("ReviewScriptQualityDialog", () => {
  beforeEach(() => {
    listProviders.mockReset();
    listModels.mockReset();
    getAiSettings.mockReset();
    createScriptQualityReview.mockReset();
    getJob.mockReset();
    findGenerationIdForJob.mockReset();
    cancelJob.mockReset();

    listProviders.mockResolvedValue([provider]);
    listModels.mockResolvedValue([model]);
    getAiSettings.mockResolvedValue(settings);
    getJob.mockResolvedValue(completedJob());
    findGenerationIdForJob.mockResolvedValue("gen-qr-1");
  });

  it("shows advisory copy and duration/wpm fields", async () => {
    wrap(
      <ReviewScriptQualityDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        scriptTitle="Neutron Stars"
        onReviewReady={vi.fn()}
      />,
    );

    expect(
      await screen.findByTestId("script-quality-review-form"),
    ).toBeInTheDocument();
    expect(screen.getByText(/AI never approves content/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Target duration/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Words per minute/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Approved$/i)).not.toBeInTheDocument();
  });

  it("uses Save Before Review when dirty and prevents duplicate submit", async () => {
    const onSaveThenReview = vi.fn().mockResolvedValue(true);
    const onReviewReady = vi.fn();
    let resolveCreate: (job: AiJob) => void = () => undefined;
    createScriptQualityReview.mockImplementation(
      () =>
        new Promise<AiJob>((resolve) => {
          resolveCreate = resolve;
        }),
    );

    const user = userEvent.setup();
    wrap(
      <ReviewScriptQualityDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        scriptTitle="Neutron Stars"
        isDirty
        onSaveThenReview={onSaveThenReview}
        onReviewReady={onReviewReady}
      />,
    );

    const submit = await screen.findByTestId("script-quality-review-submit");
    expect(submit).toHaveTextContent(/Save Before Review/i);
    await user.click(submit);
    await waitFor(() => expect(onSaveThenReview).toHaveBeenCalledTimes(1));
    expect(createScriptQualityReview).toHaveBeenCalledTimes(1);

    await user.click(submit);
    expect(createScriptQualityReview).toHaveBeenCalledTimes(1);

    resolveCreate(completedJob());
    await waitFor(() =>
      expect(onReviewReady).toHaveBeenCalledWith("gen-qr-1"),
    );
  });

  it("shows progress while the review job is running", async () => {
    createScriptQualityReview.mockResolvedValue(
      completedJob({
        status: "running",
        generation_id: null,
      }),
    );
    getJob.mockResolvedValue(
      completedJob({
        status: "running",
        generation_id: null,
      }),
    );

    const user = userEvent.setup();
    wrap(
      <ReviewScriptQualityDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        scriptTitle="Neutron Stars"
        onReviewReady={vi.fn()}
      />,
    );

    await user.click(await screen.findByTestId("script-quality-review-submit"));
    expect(
      await screen.findByTestId("script-quality-review-progress"),
    ).toHaveTextContent(/Reviewing script quality/i);
  });

  it("resolves immediately when the job already completed", async () => {
    const onReviewReady = vi.fn();
    createScriptQualityReview.mockResolvedValue(completedJob());

    const user = userEvent.setup();
    wrap(
      <ReviewScriptQualityDialog
        open
        onClose={vi.fn()}
        scriptId="sc-1"
        scriptTitle="Neutron Stars"
        onReviewReady={onReviewReady}
      />,
    );

    await user.click(await screen.findByTestId("script-quality-review-submit"));
    await waitFor(() =>
      expect(onReviewReady).toHaveBeenCalledWith("gen-qr-1"),
    );
  });
});
