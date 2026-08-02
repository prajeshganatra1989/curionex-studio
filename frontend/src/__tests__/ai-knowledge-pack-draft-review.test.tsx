import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiDraftReviewPanel } from "@/components/knowledge-packs/ai-draft-review-panel";
import { ToastProvider } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { AiGeneration } from "@/lib/ai/types";

const getGeneration = vi.fn();
const applyKnowledgePackAiDraft = vi.fn();

vi.mock("@/lib/api/ai", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/ai")>(
    "@/lib/api/ai",
  );
  return {
    ...actual,
    getGeneration: (...args: unknown[]) => getGeneration(...args),
    applyKnowledgePackAiDraft: (...args: unknown[]) =>
      applyKnowledgePackAiDraft(...args),
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

function generationFixture(overrides: Partial<AiGeneration> = {}): AiGeneration {
  return {
    id: "gen-1",
    job_id: "job-1",
    prompt_version_id: "ver-1",
    model_id: "model-1",
    provider_id: "prov-openai",
    input_variables: { topic: "Neutron stars" },
    output_text: null,
    structured_output: {
      research: "Neutron stars are collapsed stellar cores.",
      facts: ["Fact one", "Fact two"],
      sources: [
        {
          label: "Astronomy Handbook",
          reference: "https://example.com/handbook",
          verification_status: "unverified",
        },
      ],
      audience: "Curious teens",
      content_angle: "Extreme physics angle",
      key_insights: ["Insight one"],
      additional_context: "",
      warnings: ["Some claims are speculative."],
    },
    purpose: "knowledge_pack.draft",
    knowledge_pack_id: "kp-1",
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

describe("AiDraftReviewPanel", () => {
  beforeEach(() => {
    getGeneration.mockReset();
    applyKnowledgePackAiDraft.mockReset();
    getGeneration.mockResolvedValue(generationFixture());
  });

  it("renders applyable sections and flags sources as unverified", async () => {
    wrap(
      <AiDraftReviewPanel
        knowledgePackId="kp-1"
        generationId="gen-1"
        currentSectionContents={{}}
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("ai-draft-review-panel")).toBeInTheDocument();
    expect(screen.getByTestId("ai-draft-section-research")).toBeInTheDocument();
    expect(screen.getByTestId("ai-draft-section-sources")).toBeInTheDocument();
    expect(
      screen.getAllByText("UNVERIFIED — HUMAN CHECK REQUIRED").length,
    ).toBeGreaterThan(0);
    expect(screen.getByTestId("ai-draft-warnings")).toHaveTextContent(
      "Some claims are speculative.",
    );
  });

  it("applies the selected sections with the default reject_if_non_empty strategy", async () => {
    applyKnowledgePackAiDraft.mockResolvedValue({
      knowledge_pack: {
        id: "kp-1",
        project_id: "proj-1",
        name: "Pack",
        description: null,
        status: "draft",
        created_by: "user-1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-03T00:00:10Z",
        sections: [],
      },
      generation_id: "gen-1",
      applied_sections: ["research", "facts"],
      conflict_strategy: "reject_if_non_empty",
    });
    const onApplied = vi.fn();
    const user = userEvent.setup();

    wrap(
      <AiDraftReviewPanel
        knowledgePackId="kp-1"
        generationId="gen-1"
        currentSectionContents={{}}
        onApplied={onApplied}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("ai-draft-review-panel");
    await user.click(screen.getByTestId("ai-draft-apply-button"));

    await waitFor(() => expect(applyKnowledgePackAiDraft).toHaveBeenCalledTimes(1));
    const [, knowledgePackId, generationId, payload] =
      applyKnowledgePackAiDraft.mock.calls[0];
    expect(knowledgePackId).toBe("kp-1");
    expect(generationId).toBe("gen-1");
    expect(payload.conflict_strategy).toBe("reject_if_non_empty");
    expect(payload.sections).toEqual(
      expect.arrayContaining(["research", "facts"]),
    );

    await waitFor(() =>
      expect(onApplied).toHaveBeenCalledWith({
        appliedSections: ["research", "facts"],
      }),
    );
  });

  it("shows the conflict details when the backend rejects a non-empty section", async () => {
    applyKnowledgePackAiDraft.mockRejectedValue(
      new ApiError(409, "Selected sections already contain content.", {
        message: "Selected sections already contain content.",
        conflicts: ["research"],
      }),
    );
    const user = userEvent.setup();

    wrap(
      <AiDraftReviewPanel
        knowledgePackId="kp-1"
        generationId="gen-1"
        currentSectionContents={{ research: "Existing research notes." }}
        onApplied={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("ai-draft-review-panel");
    expect(screen.getByText("Has existing content")).toBeInTheDocument();

    await user.click(screen.getByTestId("ai-draft-apply-button"));

    expect(
      await screen.findByTestId("ai-draft-apply-error"),
    ).toHaveTextContent("Selected sections already contain content.");
    expect(screen.getByTestId("ai-draft-apply-error")).toHaveTextContent(
      "Research",
    );
    expect(applyKnowledgePackAiDraft).toHaveBeenCalledTimes(1);
  });

  it("asks for confirmation before replacing existing content", async () => {
    applyKnowledgePackAiDraft.mockResolvedValue({
      knowledge_pack: {
        id: "kp-1",
        project_id: "proj-1",
        name: "Pack",
        description: null,
        status: "draft",
        created_by: "user-1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-03T00:00:10Z",
        sections: [],
      },
      generation_id: "gen-1",
      applied_sections: ["research"],
      conflict_strategy: "replace_selected",
    });
    const onApplied = vi.fn();
    const user = userEvent.setup();

    wrap(
      <AiDraftReviewPanel
        knowledgePackId="kp-1"
        generationId="gen-1"
        currentSectionContents={{ research: "Existing research notes." }}
        onApplied={onApplied}
        onClose={vi.fn()}
      />,
    );

    await screen.findByTestId("ai-draft-review-panel");
    await user.selectOptions(
      screen.getByLabelText("If a section already has content"),
      "replace_selected",
    );
    await user.click(screen.getByTestId("ai-draft-apply-button"));

    expect(await screen.findByTestId("ai-draft-confirm")).toBeInTheDocument();
    expect(applyKnowledgePackAiDraft).not.toHaveBeenCalled();

    await user.click(screen.getByTestId("ai-draft-confirm-apply"));

    await waitFor(() => expect(applyKnowledgePackAiDraft).toHaveBeenCalledTimes(1));
    expect(applyKnowledgePackAiDraft.mock.calls[0][3].conflict_strategy).toBe(
      "replace_selected",
    );
    await waitFor(() => expect(onApplied).toHaveBeenCalled());
  });
});
