import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScriptQualityPanel } from "@/components/scripts/script-quality-panel";
import type { AiGeneration } from "@/lib/ai/types";
import { SCRIPT_QUALITY_DIMENSIONS } from "@/lib/ai/types";

const getLatestScriptQualityReview = vi.fn();

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    getLatestScriptQualityReview: (...args: unknown[]) =>
      getLatestScriptQualityReview(...args),
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

function dimension(score = 80) {
  return {
    score,
    assessment: "ok",
    strengths: [],
    issues: [],
    suggested_action: "",
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
      overall_score: 76,
      quality_band: "needs_refinement",
      quality_band_label: "Needs Refinement",
      confidence: "medium",
      summary: "Needs a stronger hook.",
      dimensions,
      priority_issues: [],
      factual_risks: [],
      pacing_analysis: {
        estimated_word_count: 120,
        estimated_duration_seconds: 48,
        target_duration_seconds: 60,
        status: "short",
        slow_sections: [],
        rushed_sections: [],
      },
      promise_analysis: {
        promise_made: "Explain gravity",
        promise_delivered: false,
        explanation: "Promise soft",
      },
      recommended_next_action: "revise",
      warnings: [],
      ai_approval: false,
    },
    tokens_input: 100,
    tokens_output: 200,
    cost_usd: 0.01,
    latency_ms: 1200,
    temperature: 0.2,
    seed: null,
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
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

describe("ScriptQualityPanel", () => {
  beforeEach(() => {
    getLatestScriptQualityReview.mockReset();
  });

  it("shows empty state when no review exists", async () => {
    getLatestScriptQualityReview.mockResolvedValue(null);
    wrap(
      <ScriptQualityPanel
        projectId="proj-1"
        scriptId="sc-1"
        onReview={vi.fn()}
      />,
    );

    expect(
      await screen.findByText(/No quality review yet/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("script-quality-panel-review")).toBeEnabled();
  });

  it("shows score, band, recommendation, and open full review", async () => {
    getLatestScriptQualityReview.mockResolvedValue(generationFixture());
    wrap(
      <ScriptQualityPanel
        projectId="proj-1"
        scriptId="sc-1"
        onReview={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("script-quality-score")).toHaveTextContent(
      "76",
    );
    expect(screen.getByTestId("script-quality-band")).toHaveTextContent(
      /Needs Refinement/i,
    );
    expect(screen.getByTestId("script-quality-recommendation")).toHaveTextContent(
      /Revise/i,
    );
    expect(screen.queryByText(/^Approved$/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("script-quality-panel-open")).toHaveAttribute(
      "href",
      "/projects/proj-1/scripts/sc-1/quality-reviews/gen-qr-1",
    );
  });

  it("shows stale badge when input is stale", async () => {
    getLatestScriptQualityReview.mockResolvedValue(
      generationFixture({ stale_input: true }),
    );
    wrap(
      <ScriptQualityPanel
        projectId="proj-1"
        scriptId="sc-1"
        onReview={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("script-quality-stale")).toHaveTextContent(
      /Stale input/i,
    );
  });

  it("disables review when master script is empty", async () => {
    getLatestScriptQualityReview.mockResolvedValue(null);
    const onReview = vi.fn();
    wrap(
      <ScriptQualityPanel
        projectId="proj-1"
        scriptId="sc-1"
        hasMasterScript={false}
        onReview={onReview}
      />,
    );

    const button = await screen.findByTestId("script-quality-panel-review");
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(onReview).not.toHaveBeenCalled();
  });

  it("invokes onReview from the panel CTA", async () => {
    getLatestScriptQualityReview.mockResolvedValue(null);
    const onReview = vi.fn();
    const user = userEvent.setup();
    wrap(
      <ScriptQualityPanel
        projectId="proj-1"
        scriptId="sc-1"
        onReview={onReview}
      />,
    );

    await user.click(await screen.findByTestId("script-quality-panel-review"));
    await waitFor(() => expect(onReview).toHaveBeenCalledTimes(1));
  });
});
