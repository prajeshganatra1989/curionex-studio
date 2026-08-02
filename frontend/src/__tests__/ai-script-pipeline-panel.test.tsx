import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ScriptAiPipelinePanel } from "@/components/scripts/script-ai-pipeline-panel";

describe("ScriptAiPipelinePanel", () => {
  it("shows three stages and blocks later stages until prerequisites exist", () => {
    render(
      <ScriptAiPipelinePanel
        contents={{
          discovery_brief: "",
          story_spine: "",
          master_script: "",
        }}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByTestId("script-ai-pipeline-panel")).toBeInTheDocument();
    expect(
      screen.getByTestId("script-ai-pipeline-stage-discovery_brief"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("script-ai-pipeline-generate-story_spine"),
    ).toBeDisabled();
    expect(
      screen.getByTestId("script-ai-pipeline-generate-master_script"),
    ).toBeDisabled();
    expect(
      screen.getByTestId("script-ai-pipeline-generate-discovery_brief"),
    ).not.toBeDisabled();
  });

  it("suggests the next generate action without auto-applying", async () => {
    const onGenerate = vi.fn();
    const user = userEvent.setup();

    render(
      <ScriptAiPipelinePanel
        contents={{
          discovery_brief: "A".repeat(100),
          story_spine: "",
          master_script: "",
        }}
        onGenerate={onGenerate}
      />,
    );

    expect(screen.getByTestId("script-ai-pipeline-next")).toHaveTextContent(
      /Generate Story Spine/i,
    );
    await user.click(screen.getByTestId("script-ai-pipeline-next"));
    expect(onGenerate).toHaveBeenCalledWith("story_spine");
  });

  it("never claims auto-apply in copy", () => {
    render(
      <ScriptAiPipelinePanel
        contents={{
          discovery_brief: "",
          story_spine: "",
          master_script: "",
        }}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByTestId("script-ai-pipeline-panel")).toHaveTextContent(
      /never auto-applied/i,
    );
  });
});
