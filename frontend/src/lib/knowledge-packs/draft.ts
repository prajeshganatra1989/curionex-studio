/**
 * Client-side mirror of the backend's Knowledge Pack draft schema + plain-text
 * conversion (see `backend/app/ai/knowledge_pack_draft.py`). Keeping this logic
 * in the frontend lets the review panel preview exactly what will be written
 * to each section before the apply request is sent.
 */

import type {
  KnowledgePackApplyableSection,
  KnowledgePackDraft,
  KnowledgePackDraftSource,
} from "@/lib/ai/types";

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function asSources(value: unknown): KnowledgePackDraftSource[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      label: asString(item.label),
      reference: asString(item.reference),
      verification_status: "unverified" as const,
    }));
}

/** Parses a generation's `structured_output` into a typed draft, or null if unavailable. */
export function parseKnowledgePackDraft(value: unknown): KnowledgePackDraft | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  return {
    research: asString(raw.research),
    facts: asStringArray(raw.facts),
    sources: asSources(raw.sources),
    audience: asString(raw.audience),
    content_angle: asString(raw.content_angle),
    key_insights: asStringArray(raw.key_insights),
    additional_context: asString(raw.additional_context),
    warnings: asStringArray(raw.warnings),
  };
}

/** Converts one structured field into the same plain text the backend would write. */
export function draftSectionToPlainText(
  sectionKey: KnowledgePackApplyableSection,
  draft: KnowledgePackDraft,
): string {
  switch (sectionKey) {
    case "research":
      return draft.research.trim();
    case "audience":
      return draft.audience.trim();
    case "content_angle":
      return draft.content_angle.trim();
    case "additional_context":
      return draft.additional_context.trim();
    case "facts":
      return draft.facts.map((item) => `- ${item}`).join("\n");
    case "key_insights":
      return draft.key_insights.map((item) => `- ${item}`).join("\n");
    case "sources":
      return draft.sources
        .map(
          (source) =>
            `- ${source.label}: ${source.reference} [UNVERIFIED — HUMAN CHECK REQUIRED]`,
        )
        .join("\n");
    default:
      return "";
  }
}

export function draftSectionIsEmpty(
  sectionKey: KnowledgePackApplyableSection,
  draft: KnowledgePackDraft,
): boolean {
  return draftSectionToPlainText(sectionKey, draft).trim().length === 0;
}
