import { describe, expect, it } from "vitest";

import {
  discoveryBriefToPlainText,
  masterScriptToPlainText,
  parseScriptDraft,
  scriptDraftToPlainText,
  targetWordRange,
} from "@/lib/scripts/draft";

describe("script draft helpers", () => {
  it("converts discovery brief structured output to plain text", () => {
    const parsed = parseScriptDraft("discovery_brief", {
      topic: "Black holes",
      working_title: "Edge of light",
      core_question: "What happens at the event horizon?",
      viewer_promise: "A clear mental model",
      target_audience: "Curious adults",
      core_takeaway: "Nothing escapes",
      content_angle: "Physics first",
      key_facts: ["Fact A"],
      claims_requiring_verification: ["Claim A"],
      source_notes: ["Note A"],
      emotional_direction: "Wonder",
      visual_opportunities: ["Accretion disk"],
      risks_and_cautions: ["No sci-fi fluff"],
      recommended_duration_seconds: 60,
    });

    expect(parsed).not.toBeNull();
    if (!parsed || parsed.documentType !== "discovery_brief") {
      throw new Error("expected discovery brief");
    }
    const text = discoveryBriefToPlainText(parsed.draft);
    expect(text).toContain("TOPIC\nBlack holes");
    expect(text).toContain("CLAIMS REQUIRING VERIFICATION\n- Claim A");
    expect(scriptDraftToPlainText(parsed)).toBe(text);
  });

  it("applies only narration for master script plain text", () => {
    const parsed = parseScriptDraft("master_script", {
      title: "Title",
      narration: "Spoken words only.",
      hook: "Hook",
      ending: "Ending",
      estimated_word_count: 3,
      estimated_duration_seconds: 5,
      on_screen_keywords: ["kw"],
      claims_requiring_verification: [],
      editor_notes: ["note"],
      quality_checks: {
        single_core_idea: true,
        clear_hook: true,
        clear_payoff: true,
        duration_target_met: true,
      },
    });

    expect(parsed).not.toBeNull();
    if (!parsed || parsed.documentType !== "master_script") {
      throw new Error("expected master script");
    }
    expect(masterScriptToPlainText(parsed.draft)).toBe("Spoken words only.");
  });

  it("computes target word range with ±10% tolerance", () => {
    const range = targetWordRange(60, 150);
    expect(range.target).toBe(150);
    expect(range.low).toBe(135);
    expect(range.high).toBe(165);
  });
});
