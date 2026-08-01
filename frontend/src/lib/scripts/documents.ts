/** Frontend document catalog — mirrors backend DOCUMENT_CATALOG. */

import type { ScriptDocumentType } from "@/lib/api/types";

export type DocumentMeta = {
  type: ScriptDocumentType;
  title: string;
  description: string;
  guidance: string;
  /** Minimum trimmed characters for structural "complete" (UI-only). */
  completeMinChars: number;
};

export const DOCUMENT_ORDER: DocumentMeta[] = [
  {
    type: "discovery_brief",
    title: "Discovery Brief",
    description:
      "Define the topic, audience, viewer promise, core takeaway and factual direction.",
    guidance:
      "Outline the topic, who it is for, the promise to the viewer, the takeaway, and the factual direction.",
    completeMinChars: 80,
  },
  {
    type: "story_spine",
    title: "Story Spine",
    description: "Shape the hook, mystery, explanation, twist and ending.",
    guidance:
      "Map the hook, mystery, explanation, twist, and ending before writing narration.",
    completeMinChars: 80,
  },
  {
    type: "master_script",
    title: "Master Script",
    description: "Write the final narration exactly as it should be spoken.",
    guidance:
      "Write the spoken narration for the Short. Keep it tight and speakable.",
    completeMinChars: 120,
  },
];

export const DOCUMENT_BY_TYPE: Record<ScriptDocumentType, DocumentMeta> =
  Object.fromEntries(DOCUMENT_ORDER.map((item) => [item.type, item])) as Record<
    ScriptDocumentType,
    DocumentMeta
  >;
