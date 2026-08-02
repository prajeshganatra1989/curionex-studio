import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScriptQualityReviewView } from "@/components/scripts/script-quality-review-view";
import { ToastProvider } from "@/components/ui/toast";
import type { AiGeneration } from "@/lib/ai/types";
import { SCRIPT_QUALITY_DIMENSIONS } from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";

const getGeneration = vi.fn();
const applyScriptQualitySuggestion = vi.fn();

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    getGeneration: (...args: unknown[]) => getGeneration(...args),
    applyScriptQualitySuggestion: (...args: unknown[]) =>
      applyScriptQualitySuggestion(...args),
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

function dimension(score = 80) {
  return {
    score,
    assessment: "Solid",
    strengths: ["clear"],
    issues: ["minor"],
    suggested_action: "Tighten",
  };
}

function generationFixture(
  overrides: Partial<AiGeneration> = {},
): AiGeneration {
  const dimensions = Object.fromEntries(
    SCRIPT_QUALITY_DIMENSIONS.map((key) => [key, dimension()]),
  );
  return {
    id: "gen-qr-1",
    job_id: "job-1",
    prompt_version_id: "pv-1",
    model_id: "model-1",
    provider_id: "prov-1",
    input_variables: {},
    output_text: null,
    purpose: "script.quality_review",
    script_id: "sc-1",
    project_id: "proj-1",
    document_type: "master_script",
    structured_output: {
      overall_score: 84,
      model_overall_score: 90,
      quality_band: "strong",
      quality_band_label: "Strong",
      confidence: "high",
      summary: "Strong draft with one risky claim.",
      dimensions,
      priority_issues: [
        {
          id: "iss-low",
          severity: "low",
          category: "language",
          location_hint: "ending",
          original_excerpt: "kinda cool",
          problem: "informal",
          recommended_change: "formalize",
          suggested_rewrite: "striking",
        },
        {
          id: "iss-crit",
          severity: "critical",
          category: "fact",
          location_hint: "hook",
          original_excerpt: "Stars explode instantly",
          problem: "Overstated",
          recommended_change: "Soften",
          suggested_rewrite: "Stars can end violently",
        },
      ],
      factual_risks: [
        {
          claim: "Stars explode instantly",
          risk_level: "high",
          reason: "Needs sourcing",
          verification_needed: true,
          related_source_note: null,
        },
      ],
      pacing_analysis: {
        estimated_word_count: 150,
        estimated_duration_seconds: 60,
        target_duration_seconds: 60,
        target_words_per_minute: 150,
        status: "within_range",
        slow_sections: ["middle explanation"],
        rushed_sections: ["ending"],
        source: "server_metrics_plus_ai_sections",
      },
      promise_analysis: {
        promise_made: "Explain stellar death",
        promise_delivered: true,
        explanation: "Payoff lands",
      },
      recommended_next_action: "human_review",
      deterministic_metrics: {
        word_count: 148,
        estimated_duration_seconds: 59,
        target_duration_seconds: 60,
        target_words_per_minute: 150,
        pacing_status: "within_range",
      },
      warnings: [],
      ai_approval: false,
    },
    tokens_input: 100,
    tokens_output: 200,
    cost_usd: 0.02,
    latency_ms: 2000,
    temperature: 0.2,
    seed: null,
    applied_sections: [],
    stale_input: false,
    created_at: "2026-01-04T00:00:00Z",
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

describe("ScriptQualityReviewView", () => {
  beforeEach(() => {
    getGeneration.mockReset();
    applyScriptQualitySuggestion.mockReset();
    getGeneration.mockResolvedValue(generationFixture());
  });

  it("renders scorecard, severity-ordered issues, factual risks, and pacing", async () => {
    wrap(
      <ScriptQualityReviewView scriptId="sc-1" generationId="gen-qr-1" />,
    );

    expect(
      await screen.findByTestId("script-quality-review-view"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("script-quality-advisory-badge")).toHaveTextContent(
      /Ready for Human Review/i,
    );
    expect(screen.queryByText(/^Approved$/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("script-quality-scorecard")).toHaveTextContent(
      "84",
    );

    const issues = screen.getByTestId("script-quality-priority-issues");
    const issueItems = within(issues).getAllByTestId(/script-quality-issue-/);
    expect(issueItems[0]).toHaveAttribute(
      "data-testid",
      "script-quality-issue-iss-crit",
    );
    expect(issueItems[1]).toHaveAttribute(
      "data-testid",
      "script-quality-issue-iss-low",
    );

    expect(screen.getByTestId("script-quality-factual-risks")).toHaveTextContent(
      /Human verification required/i,
    );
    expect(screen.getByTestId("script-quality-promise-pacing")).toHaveTextContent(
      /Deterministic words/i,
    );
    expect(screen.getByTestId("script-quality-promise-pacing")).toHaveTextContent(
      /Slow sections \(AI\)/i,
    );
  });

  it("confirms before applying a suggestion", async () => {
    applyScriptQualitySuggestion.mockResolvedValue({
      document: {
        id: "doc-1",
        script_id: "sc-1",
        document_type: "master_script",
        title: "Master Script",
        content: "updated",
        position: 3,
        created_at: "",
        updated_at: "",
      },
      generation_id: "gen-qr-1",
      issue_id: "iss-crit",
      strategy: "replace_excerpt",
      stale_input: false,
    });

    const onApplied = vi.fn();
    const user = userEvent.setup();
    wrap(
      <ScriptQualityReviewView
        scriptId="sc-1"
        generationId="gen-qr-1"
        onApplied={onApplied}
      />,
    );

    await user.click(
      await screen.findByTestId("script-quality-apply-iss-crit"),
    );
    expect(
      await screen.findByTestId("script-quality-apply-confirm"),
    ).toBeInTheDocument();
    await user.click(screen.getByTestId("script-quality-apply-confirm-submit"));

    await waitFor(() =>
      expect(applyScriptQualitySuggestion).toHaveBeenCalledWith(
        expect.anything(),
        "sc-1",
        "gen-qr-1",
        "iss-crit",
        { strategy: "replace_excerpt" },
      ),
    );
    expect(onApplied).toHaveBeenCalled();
  });

  it("blocks apply when the review is stale", async () => {
    getGeneration.mockResolvedValue(generationFixture({ stale_input: true }));
    const user = userEvent.setup();
    wrap(
      <ScriptQualityReviewView scriptId="sc-1" generationId="gen-qr-1" />,
    );

    const applyButton = await screen.findByTestId(
      "script-quality-apply-iss-crit",
    );
    expect(applyButton).toBeDisabled();
    expect(applyButton).toHaveTextContent(/Blocked \(stale\)/i);
    expect(screen.getByTestId("script-quality-stale-banner")).toBeInTheDocument();
    await user.click(applyButton);
    expect(applyScriptQualitySuggestion).not.toHaveBeenCalled();
  });

  it("surfaces apply conflicts without auto-retry", async () => {
    applyScriptQualitySuggestion.mockRejectedValue(
      new ApiError(409, "Original excerpt not found in current Master Script."),
    );
    const user = userEvent.setup();
    wrap(
      <ScriptQualityReviewView scriptId="sc-1" generationId="gen-qr-1" />,
    );

    await user.click(
      await screen.findByTestId("script-quality-apply-iss-crit"),
    );
    await user.click(
      await screen.findByTestId("script-quality-apply-confirm-submit"),
    );
    const confirm = await screen.findByTestId("script-quality-apply-confirm");
    expect(
      within(confirm).getByText(/Original excerpt not found/i),
    ).toBeInTheDocument();
  });
});
