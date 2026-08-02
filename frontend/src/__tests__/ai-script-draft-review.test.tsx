import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScriptAiDraftReviewPanel } from "@/components/scripts/script-ai-draft-review-panel";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiGeneration } from "@/lib/ai/types";

const getGeneration = vi.fn();
const applyScriptAiDraft = vi.fn();

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    getGeneration: (...args: unknown[]) => getGeneration(...args),
    applyScriptAiDraft: (...args: unknown[]) => applyScriptAiDraft(...args),
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

function discoveryGeneration(
  overrides: Partial<AiGeneration> = {},
): AiGeneration {
  return {
    id: "gen-1",
    job_id: "job-1",
    prompt_version_id: "ver-1",
    model_id: "model-1",
    provider_id: "prov-openai",
    input_variables: { language: "English", tone: "curious" },
    output_text: null,
    structured_output: {
      topic: "Neutron stars",
      working_title: "What crushes a star?",
      core_question: "How dense can matter get?",
      viewer_promise: "A clear picture of extreme density.",
      target_audience: "Curious teens",
      core_takeaway: "Neutron stars are collapsed cores.",
      content_angle: "Extreme physics",
      key_facts: ["Fact one"],
      claims_requiring_verification: ["Claim about density"],
      source_notes: ["Astronomy handbook"],
      emotional_direction: "Awe",
      visual_opportunities: ["Star collapse"],
      risks_and_cautions: ["Avoid sensationalism"],
      recommended_duration_seconds: 60,
    },
    purpose: "script.discovery_brief.draft",
    script_id: "sc-1",
    document_type: "discovery_brief",
    project_id: "proj-1",
    tokens_input: 500,
    tokens_output: 300,
    tokens_total: 800,
    cost_usd: 0.012,
    latency_ms: 1200,
    provider_request_id: "req-1",
    model_identifier: "gpt-4o",
    temperature: 0.7,
    seed: null,
    applied_sections: [],
    applied_at: null,
    warnings: ["Some claims are speculative."],
    stale_input: false,
    created_at: "2026-01-03T00:00:00Z",
    ...overrides,
  };
}

function masterGeneration(overrides: Partial<AiGeneration> = {}): AiGeneration {
  return discoveryGeneration({
    purpose: "script.master_script.draft",
    document_type: "master_script",
    input_variables: {
      target_duration_seconds: "60",
      target_words_per_minute: "150",
    },
    structured_output: {
      title: "Collapsed Light",
      narration:
        "Imagine a star so dense a teaspoon of it outweighs a mountain. That is a neutron star.",
      hook: "Imagine a teaspoon heavier than a mountain.",
      ending: "The densest matter we know sits in silence.",
      estimated_word_count: 28,
      estimated_duration_seconds: 12,
      on_screen_keywords: ["neutron star", "density"],
      claims_requiring_verification: ["Teaspoon mass claim"],
      editor_notes: ["Keep pacing brisk"],
      quality_checks: {
        single_core_idea: true,
        clear_hook: true,
        clear_payoff: true,
        duration_target_met: false,
      },
    },
    ...overrides,
  });
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

describe("ScriptAiDraftReviewPanel", () => {
  beforeEach(() => {
    getGeneration.mockReset();
    applyScriptAiDraft.mockReset();
    getGeneration.mockResolvedValue(discoveryGeneration());
  });

  it("renders draft vs current and flags claims for verification", async () => {
    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="discovery_brief"
        generationId="gen-1"
        currentContent=""
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(
      await screen.findByTestId("script-ai-draft-review-panel"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("script-ai-generated-content")).toHaveTextContent(
      "Neutron stars",
    );
    expect(screen.getByTestId("script-ai-claims")).toHaveTextContent(
      "Claim about density",
    );
    expect(screen.getByTestId("script-ai-warnings")).toHaveTextContent(
      "Some claims are speculative.",
    );
  });

  it("shows stale input warning", async () => {
    getGeneration.mockResolvedValue(discoveryGeneration({ stale_input: true }));

    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="discovery_brief"
        generationId="gen-1"
        currentContent=""
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(
      await screen.findByTestId("script-ai-stale-warning"),
    ).toBeInTheDocument();
  });

  it("shows master metrics and duration mismatch", async () => {
    getGeneration.mockResolvedValue(masterGeneration());

    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="master_script"
        generationId="gen-1"
        currentContent=""
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("script-ai-master-meta")).toBeInTheDocument();
    expect(screen.getByTestId("script-ai-duration-mismatch")).toBeInTheDocument();
    expect(screen.getByText(/neutron star, density/i)).toBeInTheDocument();
    expect(screen.getByText("Keep pacing brisk")).toBeInTheDocument();
  });

  it("applies with reject_if_non_empty by default", async () => {
    applyScriptAiDraft.mockResolvedValue({
      document: {
        id: "doc-1",
        script_id: "sc-1",
        document_type: "discovery_brief",
        title: "Discovery Brief",
        content: "TOPIC\nNeutron stars",
        position: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-03T00:00:10Z",
      },
      generation_id: "gen-1",
      conflict_strategy: "reject_if_non_empty",
      stale_input: false,
    });
    const onApplied = vi.fn();
    const user = userEvent.setup();

    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="discovery_brief"
        generationId="gen-1"
        currentContent=""
        onApplied={onApplied}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("script-ai-draft-review-panel");
    await user.click(screen.getByTestId("script-ai-apply-button"));

    await waitFor(() => expect(applyScriptAiDraft).toHaveBeenCalledTimes(1));
    const [, scriptId, documentType, generationId, payload] =
      applyScriptAiDraft.mock.calls[0];
    expect(scriptId).toBe("sc-1");
    expect(documentType).toBe("discovery_brief");
    expect(generationId).toBe("gen-1");
    expect(payload.conflict_strategy).toBe("reject_if_non_empty");
    await waitFor(() => expect(onApplied).toHaveBeenCalled());
  });

  it("shows conflict error when reject_if_non_empty fails", async () => {
    applyScriptAiDraft.mockRejectedValue(
      new ApiError(409, "Document already contains content.", {
        message: "Document already contains content.",
        conflicts: ["discovery_brief"],
      }),
    );
    const user = userEvent.setup();

    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="discovery_brief"
        generationId="gen-1"
        currentContent="Existing brief content."
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("script-ai-draft-review-panel");
    expect(screen.getByText("Has existing content")).toBeInTheDocument();
    await user.click(screen.getByTestId("script-ai-apply-button"));

    expect(await screen.findByTestId("script-ai-apply-error")).toHaveTextContent(
      "Document already contains content.",
    );
  });

  it("asks for confirmation before replace", async () => {
    applyScriptAiDraft.mockResolvedValue({
      document: {
        id: "doc-1",
        script_id: "sc-1",
        document_type: "discovery_brief",
        title: "Discovery Brief",
        content: "TOPIC\nNeutron stars",
        position: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-03T00:00:10Z",
      },
      generation_id: "gen-1",
      conflict_strategy: "replace",
      stale_input: false,
    });
    const user = userEvent.setup();

    wrap(
      <ScriptAiDraftReviewPanel
        scriptId="sc-1"
        documentType="discovery_brief"
        generationId="gen-1"
        currentContent="Existing brief content."
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("script-ai-draft-review-panel");
    await user.selectOptions(
      screen.getByLabelText("If this document already has content"),
      "replace",
    );
    await user.click(screen.getByTestId("script-ai-apply-button"));

    expect(await screen.findByTestId("script-ai-confirm")).toBeInTheDocument();
    expect(applyScriptAiDraft).not.toHaveBeenCalled();

    await user.click(screen.getByTestId("script-ai-confirm-apply"));
    await waitFor(() => expect(applyScriptAiDraft).toHaveBeenCalledTimes(1));
    expect(applyScriptAiDraft.mock.calls[0][4].conflict_strategy).toBe("replace");
  });
});
