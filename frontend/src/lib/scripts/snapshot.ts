import type { ScriptDocumentType } from "@/lib/api/types";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";

export type SnapshotSection = {
  key: ScriptDocumentType;
  title: string;
  content: string;
};

export type ParsedSnapshot = {
  sections: SnapshotSection[];
  raw: string;
};

const HEADER_BY_TYPE: Record<ScriptDocumentType, string> = {
  discovery_brief: "DISCOVERY BRIEF",
  story_spine: "STORY SPINE",
  master_script: "MASTER SCRIPT",
};

const TYPE_BY_HEADER = Object.fromEntries(
  Object.entries(HEADER_BY_TYPE).map(([type, header]) => [header, type]),
) as Record<string, ScriptDocumentType>;

/** Parse immutable ContentVersion snapshot plain text into document sections. */
export function parseSnapshot(content: string): ParsedSnapshot {
  const raw = content ?? "";
  const trimmed = raw.trim();
  if (!trimmed) {
    return {
      raw,
      sections: DOCUMENT_ORDER.map((meta) => ({
        key: meta.type,
        title: meta.title,
        content: "",
      })),
    };
  }

  const headerPattern = /^(DISCOVERY BRIEF|STORY SPINE|MASTER SCRIPT)$/m;
  const matches = [...trimmed.matchAll(new RegExp(headerPattern, "gm"))];

  const contentByType: Partial<Record<ScriptDocumentType, string>> = {};

  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index];
    if (!match || match.index === undefined) continue;
    const header = match[1]!;
    const docType = TYPE_BY_HEADER[header];
    if (!docType) continue;

    const bodyStart = match.index + match[0].length;
    const nextMatch = matches[index + 1];
    const bodyEnd =
      nextMatch && nextMatch.index !== undefined
        ? nextMatch.index
        : trimmed.length;
    const body = trimmed.slice(bodyStart, bodyEnd).trim();
    contentByType[docType] = body;
  }

  return {
    raw,
    sections: DOCUMENT_ORDER.map((meta) => ({
      key: meta.type,
      title: meta.title,
      content: contentByType[meta.type] ?? "",
    })),
  };
}
