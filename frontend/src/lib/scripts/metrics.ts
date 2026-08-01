/** Local Script Workspace metrics — structure only, never quality claims. */

import {
  DOCUMENT_BY_TYPE,
  DOCUMENT_ORDER,
  type DocumentMeta,
} from "@/lib/scripts/documents";
import type { ScriptDocumentType } from "@/lib/api/types";

/** Typical Shorts voiceover pace (configurable default). */
export const DEFAULT_NARRATION_WPM = 150;

export function countCharacters(text: string): number {
  return text.length;
}

export function countWords(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).filter(Boolean).length;
}

export function isDocumentStarted(content: string): boolean {
  return content.trim().length > 0;
}

export function isDocumentComplete(
  content: string,
  meta: DocumentMeta,
): boolean {
  return content.trim().length >= meta.completeMinChars;
}

export type DocumentCompletionState = "empty" | "started" | "complete";

export function documentCompletionState(
  content: string,
  type: ScriptDocumentType | string,
): DocumentCompletionState {
  const meta =
    DOCUMENT_BY_TYPE[type as ScriptDocumentType] ??
    DOCUMENT_ORDER.find((d) => d.type === type);
  if (!isDocumentStarted(content)) return "empty";
  if (meta && isDocumentComplete(content, meta)) return "complete";
  return "started";
}

export function completedDocumentCount(
  contents: Record<string, string>,
): number {
  return DOCUMENT_ORDER.filter((meta) =>
    isDocumentComplete(contents[meta.type] ?? "", meta),
  ).length;
}

export function workspaceCompletionPercent(
  contents: Record<string, string>,
): number {
  if (DOCUMENT_ORDER.length === 0) return 0;
  const done = completedDocumentCount(contents);
  return Math.round((done / DOCUMENT_ORDER.length) * 100);
}

export function totalWords(contents: Record<string, string>): number {
  return DOCUMENT_ORDER.reduce(
    (sum, meta) => sum + countWords(contents[meta.type] ?? ""),
    0,
  );
}

export function totalCharacters(contents: Record<string, string>): number {
  return DOCUMENT_ORDER.reduce(
    (sum, meta) => sum + countCharacters(contents[meta.type] ?? ""),
    0,
  );
}

/** Estimated narration duration in whole seconds at the given WPM. */
export function estimatedNarrationSeconds(
  wordCount: number,
  wordsPerMinute: number = DEFAULT_NARRATION_WPM,
): number {
  if (wordCount <= 0 || wordsPerMinute <= 0) return 0;
  return Math.max(1, Math.round((wordCount / wordsPerMinute) * 60));
}

export function formatNarrationEstimate(
  wordCount: number,
  wordsPerMinute: number = DEFAULT_NARRATION_WPM,
): string {
  const seconds = estimatedNarrationSeconds(wordCount, wordsPerMinute);
  if (seconds <= 0) return "Estimated voiceover: 0 seconds";
  if (seconds < 60) {
    return `Estimated voiceover: ${seconds} second${seconds === 1 ? "" : "s"}`;
  }
  const minutes = Math.floor(seconds / 60);
  const rem = seconds % 60;
  if (rem === 0) {
    return `Estimated voiceover: ${minutes} minute${minutes === 1 ? "" : "s"}`;
  }
  return `Estimated voiceover: ${minutes}m ${rem}s`;
}
