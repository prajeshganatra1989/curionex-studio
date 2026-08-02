import { describe, expect, it } from "vitest";

import { parseSnapshot } from "@/lib/scripts/snapshot";

describe("parseSnapshot", () => {
  it("parses all three snapshot sections", () => {
    const content = [
      "DISCOVERY BRIEF",
      "",
      "Brief body",
      "",
      "STORY SPINE",
      "",
      "Spine body",
      "",
      "MASTER SCRIPT",
      "",
      "Script body",
      "",
    ].join("\n");

    const parsed = parseSnapshot(content);
    expect(parsed.sections).toHaveLength(3);
    expect(parsed.sections[0]).toMatchObject({
      key: "discovery_brief",
      content: "Brief body",
    });
    expect(parsed.sections[1]).toMatchObject({
      key: "story_spine",
      content: "Spine body",
    });
    expect(parsed.sections[2]).toMatchObject({
      key: "master_script",
      content: "Script body",
    });
  });

  it("returns empty sections for blank content", () => {
    const parsed = parseSnapshot("");
    expect(parsed.sections.every((section) => section.content === "")).toBe(
      true,
    );
  });
});
