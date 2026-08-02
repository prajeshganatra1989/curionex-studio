import { describe, expect, it } from "vitest";

import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import {
  completedDocumentCount,
  countCharacters,
  countWords,
  DEFAULT_NARRATION_WPM,
  documentCompletionState,
  estimatedNarrationSeconds,
  formatNarrationEstimate,
  isDocumentComplete,
  isDocumentStarted,
  totalCharacters,
  totalWords,
  workspaceCompletionPercent,
} from "@/lib/scripts/metrics";

describe("script metrics", () => {
  it("counts words and characters", () => {
    expect(countWords("one two three")).toBe(3);
    expect(countWords("   ")).toBe(0);
    expect(countCharacters("abc")).toBe(3);
    expect(countCharacters("")).toBe(0);
  });

  it("treats empty content as zero totals", () => {
    const empty = {
      discovery_brief: "",
      story_spine: "  ",
      master_script: "",
    };
    expect(totalWords(empty)).toBe(0);
    expect(totalCharacters(empty)).toBe(2);
    expect(workspaceCompletionPercent(empty)).toBe(0);
    expect(completedDocumentCount(empty)).toBe(0);
  });

  it("computes started and complete states with thresholds", () => {
    expect(isDocumentStarted("")).toBe(false);
    expect(isDocumentStarted("hook")).toBe(true);
    expect(documentCompletionState("", "discovery_brief")).toBe("empty");
    expect(documentCompletionState("short", "discovery_brief")).toBe("started");
    const complete = "x".repeat(DOCUMENT_ORDER[0]!.completeMinChars);
    expect(isDocumentComplete(complete, DOCUMENT_ORDER[0]!)).toBe(true);
    expect(documentCompletionState(complete, "discovery_brief")).toBe("complete");
  });

  it("computes workspace completion percentage", () => {
    const contents = {
      discovery_brief: "x".repeat(80),
      story_spine: "x".repeat(80),
      master_script: "",
    };
    expect(workspaceCompletionPercent(contents)).toBe(67);
  });

  it("estimates narration duration at configurable WPM", () => {
    expect(estimatedNarrationSeconds(0)).toBe(0);
    expect(estimatedNarrationSeconds(150, DEFAULT_NARRATION_WPM)).toBe(60);
    expect(estimatedNarrationSeconds(140, 150)).toBe(56);
    expect(formatNarrationEstimate(140, 150)).toBe(
      "Estimated voiceover: 56 seconds",
    );
    expect(formatNarrationEstimate(0)).toBe("Estimated voiceover: 0 seconds");
  });
});

describe("document catalog", () => {
  it("keeps the three production documents in order", () => {
    expect(DOCUMENT_ORDER.map((d) => d.type)).toEqual([
      "discovery_brief",
      "story_spine",
      "master_script",
    ]);
  });
});
