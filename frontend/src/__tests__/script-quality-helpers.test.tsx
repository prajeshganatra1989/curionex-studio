import { describe, expect, it } from "vitest";

import type { ScriptQualityReview } from "@/lib/ai/types";
import { SCRIPT_QUALITY_DIMENSIONS } from "@/lib/ai/types";
import {
  isIssueApplied,
  parseScriptQualityReview,
  recommendationLabel,
  sortPriorityIssues,
} from "@/lib/scripts/quality";

function dimension(score = 80) {
  return {
    score,
    assessment: "ok",
    strengths: ["clear"],
    issues: [],
    suggested_action: "keep",
  };
}

function validReview(
  overrides: Partial<ScriptQualityReview> = {},
): Record<string, unknown> {
  const dimensions = Object.fromEntries(
    SCRIPT_QUALITY_DIMENSIONS.map((key) => [key, dimension()]),
  );
  return {
    overall_score: 82,
    model_overall_score: 88,
    quality_band: "strong",
    quality_band_label: "Strong",
    confidence: "medium",
    summary: "Solid draft with a few risks.",
    dimensions,
    priority_issues: [
      {
        id: "iss-2",
        severity: "medium",
        category: "clarity",
        location_hint: "middle",
        original_excerpt: "old text",
        problem: "unclear",
        recommended_change: "clarify",
        suggested_rewrite: "new text",
      },
      {
        id: "iss-1",
        severity: "critical",
        category: "fact",
        location_hint: "hook",
        original_excerpt: "claim",
        problem: "risky claim",
        recommended_change: "verify",
        suggested_rewrite: "softened claim",
      },
    ],
    factual_risks: [
      {
        claim: "Stars implode instantly",
        risk_level: "high",
        reason: "oversimplified",
        verification_needed: false,
        related_source_note: null,
      },
    ],
    pacing_analysis: {
      estimated_word_count: 140,
      estimated_duration_seconds: 56,
      target_duration_seconds: 60,
      status: "within_range",
      slow_sections: ["setup"],
      rushed_sections: [],
    },
    promise_analysis: {
      promise_made: "Explain neutron stars",
      promise_delivered: true,
      explanation: "Payoff lands",
    },
    recommended_next_action: "human_review",
    warnings: [],
    ai_approval: true,
    ...overrides,
  };
}

describe("script quality helpers", () => {
  it("parses structured review and forces advisory flags", () => {
    const review = parseScriptQualityReview(validReview());
    expect(review).not.toBeNull();
    expect(review!.overall_score).toBe(82);
    expect(review!.quality_band_label).toBe("Strong");
    expect(review!.ai_approval).toBe(false);
    expect(review!.factual_risks[0]!.verification_needed).toBe(true);
    expect(review!.priority_issues[0]!.id).toBe("iss-1");
    expect(review!.priority_issues[1]!.id).toBe("iss-2");
  });

  it("sorts priority issues by severity then id", () => {
    const sorted = sortPriorityIssues([
      {
        id: "b",
        severity: "high",
        category: "clarity",
        location_hint: "",
        original_excerpt: "",
        problem: "",
        recommended_change: "",
        suggested_rewrite: null,
      },
      {
        id: "a",
        severity: "critical",
        category: "fact",
        location_hint: "",
        original_excerpt: "",
        problem: "",
        recommended_change: "",
        suggested_rewrite: null,
      },
      {
        id: "c",
        severity: "high",
        category: "pacing",
        location_hint: "",
        original_excerpt: "",
        problem: "",
        recommended_change: "",
        suggested_rewrite: null,
      },
    ]);
    expect(sorted.map((item) => item.id)).toEqual(["a", "b", "c"]);
  });

  it("never labels recommendations as Approved", () => {
    expect(recommendationLabel("revise")).toBe("Revise");
    expect(recommendationLabel("human_review")).toBe("Ready for Human Review");
    expect(recommendationLabel("ready_for_version")).toBe("Ready for Version");
    expect(recommendationLabel("approved")).not.toMatch(/approved/i);
  });

  it("tracks applied suggestions via issue keys", () => {
    expect(
      isIssueApplied(
        {
          id: "g1",
          job_id: "j1",
          prompt_version_id: "p1",
          model_id: "m1",
          provider_id: "pr1",
          input_variables: {},
          output_text: null,
          tokens_input: null,
          tokens_output: null,
          cost_usd: null,
          latency_ms: null,
          temperature: null,
          seed: null,
          created_at: "",
          applied_sections: ["issue:iss-1"],
        },
        "iss-1",
      ),
    ).toBe(true);
    expect(
      isIssueApplied(
        {
          id: "g1",
          job_id: "j1",
          prompt_version_id: "p1",
          model_id: "m1",
          provider_id: "pr1",
          input_variables: {},
          output_text: null,
          tokens_input: null,
          tokens_output: null,
          cost_usd: null,
          latency_ms: null,
          temperature: null,
          seed: null,
          created_at: "",
          applied_sections: [],
        },
        "iss-1",
      ),
    ).toBe(false);
  });

  it("rejects incomplete structured payloads", () => {
    expect(parseScriptQualityReview({ overall_score: 50 })).toBeNull();
  });
});
