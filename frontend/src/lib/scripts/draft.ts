/**
 * Client-side mirror of backend script draft schemas + plain-text conversion
 * (`backend/app/ai/script_draft.py`). Used by the review panel to preview
 * exactly what will be written before apply.
 */

import type { ScriptAiDocumentType } from "@/lib/ai/types";

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter(Boolean);
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function bullets(items: string[]): string {
  return items.length > 0 ? items.map((item) => `- ${item}`).join("\n") : "- (none)";
}

export type DiscoveryBriefDraft = {
  topic: string;
  working_title: string;
  core_question: string;
  viewer_promise: string;
  target_audience: string;
  core_takeaway: string;
  content_angle: string;
  key_facts: string[];
  claims_requiring_verification: string[];
  source_notes: string[];
  emotional_direction: string;
  visual_opportunities: string[];
  risks_and_cautions: string[];
  recommended_duration_seconds: number;
};

export type StoryBeat = {
  beat: number;
  purpose: string;
  content: string;
  estimated_seconds: number;
};

export type StorySpineDraft = {
  hook: string;
  setup: string;
  curiosity_gap: string;
  progression: StoryBeat[];
  core_explanation: string;
  reveal_or_reframe: string;
  ending: string;
  call_to_action: string;
  visual_rhythm_notes: string[];
  retention_risks: string[];
  claims_requiring_verification: string[];
  estimated_total_seconds: number;
};

export type MasterScriptDraft = {
  title: string;
  narration: string;
  hook: string;
  ending: string;
  estimated_word_count: number;
  estimated_duration_seconds: number;
  on_screen_keywords: string[];
  claims_requiring_verification: string[];
  editor_notes: string[];
  quality_checks: {
    single_core_idea: boolean;
    clear_hook: boolean;
    clear_payoff: boolean;
    duration_target_met: boolean;
  };
};

export type ScriptStructuredDraft =
  | { documentType: "discovery_brief"; draft: DiscoveryBriefDraft }
  | { documentType: "story_spine"; draft: StorySpineDraft }
  | { documentType: "master_script"; draft: MasterScriptDraft };

export function parseDiscoveryBrief(value: unknown): DiscoveryBriefDraft | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  return {
    topic: asString(raw.topic),
    working_title: asString(raw.working_title),
    core_question: asString(raw.core_question),
    viewer_promise: asString(raw.viewer_promise),
    target_audience: asString(raw.target_audience),
    core_takeaway: asString(raw.core_takeaway),
    content_angle: asString(raw.content_angle),
    key_facts: asStringArray(raw.key_facts),
    claims_requiring_verification: asStringArray(
      raw.claims_requiring_verification,
    ),
    source_notes: asStringArray(raw.source_notes),
    emotional_direction: asString(raw.emotional_direction),
    visual_opportunities: asStringArray(raw.visual_opportunities),
    risks_and_cautions: asStringArray(raw.risks_and_cautions),
    recommended_duration_seconds: asNumber(
      raw.recommended_duration_seconds,
      60,
    ),
  };
}

export function parseStorySpine(value: unknown): StorySpineDraft | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  const progression = Array.isArray(raw.progression)
    ? raw.progression
        .filter(
          (item): item is Record<string, unknown> =>
            Boolean(item) && typeof item === "object",
        )
        .map((item) => ({
          beat: asNumber(item.beat, 0),
          purpose: asString(item.purpose),
          content: asString(item.content),
          estimated_seconds: asNumber(item.estimated_seconds, 1),
        }))
        .sort((a, b) => a.beat - b.beat)
    : [];

  return {
    hook: asString(raw.hook),
    setup: asString(raw.setup),
    curiosity_gap: asString(raw.curiosity_gap),
    progression,
    core_explanation: asString(raw.core_explanation),
    reveal_or_reframe: asString(raw.reveal_or_reframe),
    ending: asString(raw.ending),
    call_to_action: asString(raw.call_to_action),
    visual_rhythm_notes: asStringArray(raw.visual_rhythm_notes),
    retention_risks: asStringArray(raw.retention_risks),
    claims_requiring_verification: asStringArray(
      raw.claims_requiring_verification,
    ),
    estimated_total_seconds: asNumber(raw.estimated_total_seconds, 60),
  };
}

export function parseMasterScript(value: unknown): MasterScriptDraft | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  const checks =
    raw.quality_checks && typeof raw.quality_checks === "object"
      ? (raw.quality_checks as Record<string, unknown>)
      : {};
  return {
    title: asString(raw.title),
    narration: asString(raw.narration),
    hook: asString(raw.hook),
    ending: asString(raw.ending),
    estimated_word_count: asNumber(raw.estimated_word_count, 0),
    estimated_duration_seconds: asNumber(raw.estimated_duration_seconds, 60),
    on_screen_keywords: asStringArray(raw.on_screen_keywords),
    claims_requiring_verification: asStringArray(
      raw.claims_requiring_verification,
    ),
    editor_notes: asStringArray(raw.editor_notes),
    quality_checks: {
      single_core_idea: asBoolean(checks.single_core_idea, true),
      clear_hook: asBoolean(checks.clear_hook, true),
      clear_payoff: asBoolean(checks.clear_payoff, true),
      duration_target_met: asBoolean(checks.duration_target_met, true),
    },
  };
}

export function parseScriptDraft(
  documentType: ScriptAiDocumentType | string,
  value: unknown,
): ScriptStructuredDraft | null {
  if (documentType === "discovery_brief") {
    const draft = parseDiscoveryBrief(value);
    return draft ? { documentType: "discovery_brief", draft } : null;
  }
  if (documentType === "story_spine") {
    const draft = parseStorySpine(value);
    return draft ? { documentType: "story_spine", draft } : null;
  }
  if (documentType === "master_script") {
    const draft = parseMasterScript(value);
    return draft ? { documentType: "master_script", draft } : null;
  }
  return null;
}

export function discoveryBriefToPlainText(draft: DiscoveryBriefDraft): string {
  return [
    `TOPIC\n${draft.topic}`,
    `WORKING TITLE\n${draft.working_title}`,
    `CORE QUESTION\n${draft.core_question}`,
    `VIEWER PROMISE\n${draft.viewer_promise}`,
    `TARGET AUDIENCE\n${draft.target_audience}`,
    `CORE TAKEAWAY\n${draft.core_takeaway}`,
    `CONTENT ANGLE\n${draft.content_angle}`,
    `KEY FACTS\n${bullets(draft.key_facts)}`,
    `CLAIMS REQUIRING VERIFICATION\n${bullets(draft.claims_requiring_verification)}`,
    `SOURCE NOTES\n${bullets(draft.source_notes)}`,
    `EMOTIONAL DIRECTION\n${draft.emotional_direction}`,
    `VISUAL OPPORTUNITIES\n${bullets(draft.visual_opportunities)}`,
    `RISKS AND CAUTIONS\n${bullets(draft.risks_and_cautions)}`,
    `RECOMMENDED DURATION\n${draft.recommended_duration_seconds} seconds`,
  ].join("\n\n");
}

export function storySpineToPlainText(draft: StorySpineDraft): string {
  const beatLines = draft.progression.map(
    (beat) =>
      `${beat.beat}. [${beat.purpose}] (${beat.estimated_seconds}s)\n${beat.content}`,
  );
  const beatsBlock = beatLines.length > 0 ? beatLines.join("\n\n") : "(none)";
  return [
    `HOOK\n${draft.hook}`,
    `SETUP\n${draft.setup}`,
    `CURIOSITY GAP\n${draft.curiosity_gap}`,
    `STORY BEATS\n${beatsBlock}`,
    `CORE EXPLANATION\n${draft.core_explanation}`,
    `REVEAL / REFRAME\n${draft.reveal_or_reframe}`,
    `ENDING\n${draft.ending}`,
    `CALL TO ACTION\n${draft.call_to_action}`,
    `VISUAL RHYTHM NOTES\n${bullets(draft.visual_rhythm_notes)}`,
    `RETENTION RISKS\n${bullets(draft.retention_risks)}`,
    `CLAIMS REQUIRING VERIFICATION\n${bullets(draft.claims_requiring_verification)}`,
    `ESTIMATED DURATION\n${draft.estimated_total_seconds} seconds`,
  ].join("\n\n");
}

/** Master Script apply writes narration only. */
export function masterScriptToPlainText(draft: MasterScriptDraft): string {
  return draft.narration.trim();
}

export function scriptDraftToPlainText(
  parsed: ScriptStructuredDraft,
): string {
  if (parsed.documentType === "discovery_brief") {
    return discoveryBriefToPlainText(parsed.draft);
  }
  if (parsed.documentType === "story_spine") {
    return storySpineToPlainText(parsed.draft);
  }
  return masterScriptToPlainText(parsed.draft);
}

export function claimsRequiringVerification(
  parsed: ScriptStructuredDraft,
): string[] {
  return parsed.draft.claims_requiring_verification;
}

/** ±10% tolerance used by the backend duration word-count check. */
export const DURATION_WORD_COUNT_TOLERANCE = 0.1;

export function targetWordRange(
  targetDurationSeconds: number,
  targetWordsPerMinute: number,
  tolerance = DURATION_WORD_COUNT_TOLERANCE,
): { low: number; target: number; high: number } {
  const target = Math.max(
    1,
    Math.round((targetDurationSeconds / 60) * targetWordsPerMinute),
  );
  const low = Math.max(1, Math.round(target * (1 - tolerance)));
  const high = Math.round(target * (1 + tolerance));
  return { low, target, high };
}

export function prerequisiteLabels(missing: string[]): string[] {
  const titles: Record<string, string> = {
    discovery_brief: "Discovery Brief",
    story_spine: "Story Spine",
    master_script: "Master Script",
  };
  return missing.map((key) => titles[key] ?? key);
}
