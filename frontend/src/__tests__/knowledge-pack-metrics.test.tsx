import { describe, expect, it } from "vitest";

import {
  completionPercent,
  countCharacters,
  countWords,
  estimatedReadingMinutes,
  formatReadingTime,
  isSectionComplete,
} from "@/lib/knowledge-packs/metrics";
import { SECTION_ORDER } from "@/lib/knowledge-packs/sections";

describe("knowledge pack metrics", () => {
  it("counts characters", () => {
    expect(countCharacters("abc")).toBe(3);
    expect(countCharacters("")).toBe(0);
  });

  it("counts words", () => {
    expect(countWords("one two three")).toBe(3);
    expect(countWords("  spaced   words ")).toBe(2);
    expect(countWords("   ")).toBe(0);
  });

  it("estimates reading time from words", () => {
    expect(estimatedReadingMinutes(0)).toBe(0);
    expect(estimatedReadingMinutes(50)).toBe(1);
    expect(estimatedReadingMinutes(400)).toBe(2);
    expect(formatReadingTime(0)).toBe("0 min");
    expect(formatReadingTime(50)).toBe("1 min");
  });

  it("computes completion from non-empty sections", () => {
    expect(isSectionComplete("")).toBe(false);
    expect(isSectionComplete("   ")).toBe(false);
    expect(isSectionComplete("fact")).toBe(true);
    expect(completionPercent(["a", "", "b", "", "", "", ""])).toBe(29);
    expect(completionPercent(SECTION_ORDER.map(() => "x"))).toBe(100);
    expect(completionPercent(SECTION_ORDER.map(() => ""))).toBe(0);
  });
});

describe("section catalog", () => {
  it("keeps the required display order", () => {
    expect(SECTION_ORDER.map((s) => s.title)).toEqual([
      "Research",
      "Facts",
      "Sources",
      "Audience",
      "Content Angle",
      "Key Insights",
      "Additional Context",
    ]);
  });
});
