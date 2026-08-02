import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement, ReactNode } from "react";

import {
  ProductionPackagePage,
  storyboardV2ToMarkdown,
} from "@/components/scripts/production-package-page";
import type { ProductionPackage } from "@/lib/api/types";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({
    projectId: "proj-1",
    scriptId: "script-1",
  }),
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

const getScript = vi.fn();
const getEligibility = vi.fn();
const createPackage = vi.fn();

vi.mock("@/lib/api/projects", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/projects")>(
    "@/lib/api/projects",
  );
  return {
    ...actual,
    getScript: (...args: unknown[]) => getScript(...args),
    getProductionPackageEligibility: (...args: unknown[]) =>
      getEligibility(...args),
    createProductionPackage: (...args: unknown[]) => createPackage(...args),
  };
});

vi.mock("@/lib/auth/auth-context", () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => children,
  useAuth: () => ({
    api: {},
    status: "authenticated",
    user: { id: "u1", email: "owner@example.com" },
  }),
}));

function wrap(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

const samplePackage: ProductionPackage = {
  project: {
    id: "proj-1",
    project_code: "CRX-0001",
    name: "Proj",
    status: "active",
    description: null,
  },
  script: {
    id: "script-1",
    script_code: "CRX-0001-S01",
    title: "Why Do Magnets Attract?",
    status: "approved",
    description: null,
    knowledge_pack_id: null,
    project_id: "proj-1",
  },
  knowledge_pack: {
    id: null,
    name: null,
    status: null,
    description: null,
    facts: null,
    sources: null,
    content_angle: null,
    key_insights: null,
  },
  discovery_brief: "Brief",
  story_spine: "Spine",
  master_script: "A magnet isn't magical.",
  quality_review: {
    available: false,
    generation_id: null,
    overall_score: null,
    quality_band: null,
    recommended_next_action: null,
    gold_threshold_met: false,
  },
  production_metadata: {
    generated_at: new Date().toISOString(),
    gold_gate: "script_status_approved",
    target_duration_seconds: 60,
    recommended_wpm: 150,
    format: "youtube_shorts_9x16",
    blueprint_version: "1.0",
    voice_bible_version: "1.0",
    editorial_bible_version: "1.0",
    notes: "Planning package only",
  },
  storyboard: [
    {
      scene_number: 1,
      time_range: "0:00–0:04",
      start_seconds: 0,
      end_seconds: 4,
      narration: "A magnet isn't magical.",
      purpose: "hook",
      suggested_visual: "Hero",
      suggested_motion: "Static",
      suggested_on_screen_text: "Optional",
      transition: "Fade",
    },
  ],
  storyboard_v2: [
    {
      scene_number: 1,
      start_time: 0,
      end_time: 4,
      duration: 4,
      narration: "A magnet isn't magical.",
      scene_goal: "Open with a concrete moment",
      viewer_emotion: "curiosity",
      visual_type: "Macro",
      camera_movement: "Push",
      transition: "Fade",
      animation_suggestion: "Gentle push-in",
      on_screen_text: "Optional",
      text_position: "top",
      asset_required: "Macro",
      music_mood: "Curious",
      sound_effects: "None",
      notes: "Mute-picture test.",
      purpose: "hook",
    },
  ],
  shot_list: [
    {
      shot_number: 1,
      scene_number: 1,
      asset_type: "stock",
      description: "Hero",
      illustration: false,
      stock: true,
      diagram: false,
      animation: false,
      text_overlay: false,
      priority: "must",
    },
  ],
  asset_checklist: [
    {
      id: "stock_footage",
      label: "Stock Footage",
      category: "visual",
      required: true,
      notes: null,
    },
  ],
  voice_package: {
    estimated_duration_seconds: 4,
    word_count: 4,
    recommended_wpm: 150,
    pause_markers: ["Scene 1"],
    emphasis_markers: ["A magnet isn't magical."],
    pronunciation_notes: ["Verify names"],
    persona_hint: "Primary Curionex Narrator",
  },
  subtitle_package: [
    {
      index: 1,
      start_seconds: 0,
      end_seconds: 4,
      text: "A magnet isn't magical.",
      lines: ["A magnet isn't magical."],
    },
  ],
  youtube_package: {
    title: "Why Do Magnets Attract?",
    description: "Desc",
    keywords: ["magnets"],
    hashtags: ["#Curionex"],
    category: "Education",
    thumbnail_concept: "Calm frame",
  },
  qa_package: [
    {
      id: "qa_1",
      domain: "editorial",
      label: "Single takeaway is clear",
      checked: false,
    },
  ],
};

describe("ProductionPackagePage", () => {
  beforeEach(() => {
    getScript.mockReset();
    getEligibility.mockReset();
    createPackage.mockReset();
    getScript.mockResolvedValue({
      id: "script-1",
      project_id: "proj-1",
      knowledge_pack_id: null,
      script_code: "CRX-0001-S01",
      title: "Why Do Magnets Attract?",
      description: null,
      status: "approved",
      content_version_id: null,
      created_by: "u1",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      documents: [],
    });
  });

  it("blocks generate when not eligible", async () => {
    getEligibility.mockResolvedValue({
      eligible: false,
      reason: "Not gold yet",
      gold_gate: null,
      overall_score: null,
      script_status: "draft",
      has_approved_version: false,
    });
    wrap(<ProductionPackagePage />);
    expect(await screen.findByText("Gold approval required")).toBeInTheDocument();
    expect(
      screen.getByTestId("generate-production-package"),
    ).toBeDisabled();
  });

  it("generates package and shows storyboard tab", async () => {
    const user = userEvent.setup();
    getEligibility.mockResolvedValue({
      eligible: true,
      reason: "approved",
      gold_gate: "script_status_approved",
      overall_score: null,
      script_status: "approved",
      has_approved_version: false,
    });
    createPackage.mockResolvedValue(samplePackage);
    wrap(<ProductionPackagePage />);
    await screen.findByText("Production Package");
    await user.click(screen.getByTestId("generate-production-package"));
    await waitFor(() =>
      expect(createPackage).toHaveBeenCalled(),
    );
    expect(await screen.findByText("Planning only", { exact: false })).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Storyboard" }));
    expect(await screen.findByText("A magnet isn't magical.")).toBeInTheDocument();
  });

  it("shows storyboard v2 timeline cards and markdown helpers", async () => {
    const user = userEvent.setup();
    getEligibility.mockResolvedValue({
      eligible: true,
      reason: "approved",
      gold_gate: "script_status_approved",
      overall_score: null,
      script_status: "approved",
      has_approved_version: false,
    });
    createPackage.mockResolvedValue(samplePackage);
    wrap(<ProductionPackagePage />);
    await user.click(await screen.findByTestId("generate-production-package"));
    await user.click(screen.getByRole("tab", { name: "Storyboard V2" }));
    expect(await screen.findByTestId("storyboard-v2-panel")).toBeInTheDocument();
    expect(screen.getByTestId("storyboard-v2-scene-1")).toBeInTheDocument();
    expect(screen.getAllByText("Macro").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Open with a concrete moment")).toBeInTheDocument();
    expect(screen.getByTestId("copy-storyboard-v2-markdown")).toBeInTheDocument();
    expect(screen.getByTestId("export-storyboard-v2-markdown")).toBeInTheDocument();
    const md = storyboardV2ToMarkdown(samplePackage.storyboard_v2, "Board");
    expect(md).toContain("# Board");
    expect(md).toContain("## Scene 1");
    expect(md).toContain("Macro");
  });
});
