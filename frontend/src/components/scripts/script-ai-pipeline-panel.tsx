"use client";

import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import type { ScriptAiDocumentType } from "@/lib/ai/types";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import {
  documentCompletionState,
  isDocumentStarted,
} from "@/lib/scripts/metrics";

type PipelineStageStatus =
  | "empty"
  | "started"
  | "complete"
  | "blocked"
  | "ready";

type ScriptAiPipelinePanelProps = {
  contents: Record<string, string>;
  /** Which document is currently active in the workspace. */
  activeType?: string;
  readOnly?: boolean;
  onGenerate: (documentType: ScriptAiDocumentType) => void;
  onFocusDocument?: (documentType: ScriptAiDocumentType) => void;
};

function prerequisitesFor(
  documentType: ScriptAiDocumentType,
): ScriptAiDocumentType[] {
  if (documentType === "story_spine") return ["discovery_brief"];
  if (documentType === "master_script") {
    return ["discovery_brief", "story_spine"];
  }
  return [];
}

function stageStatus(
  documentType: ScriptAiDocumentType,
  contents: Record<string, string>,
): PipelineStageStatus {
  const content = contents[documentType] ?? "";
  const completion = documentCompletionState(content, documentType);
  if (completion === "complete") return "complete";
  if (completion === "started") return "started";

  const missing = prerequisitesFor(documentType).filter(
    (dep) => !isDocumentStarted(contents[dep] ?? ""),
  );
  if (missing.length > 0) return "blocked";
  return "ready";
}

function statusLabel(status: PipelineStageStatus): string {
  switch (status) {
    case "complete":
      return "complete";
    case "started":
      return "in_progress";
    case "ready":
      return "ready";
    case "blocked":
      return "blocked";
    default:
      return "queued";
  }
}

function nextAction(
  contents: Record<string, string>,
): {
  documentType: ScriptAiDocumentType;
  label: string;
} | null {
  for (const meta of DOCUMENT_ORDER) {
    const type = meta.type as ScriptAiDocumentType;
    const status = stageStatus(type, contents);
    if (status === "blocked" || status === "complete") continue;
    if (status === "ready" || status === "empty") {
      return {
        documentType: type,
        label: `Generate ${meta.title}`,
      };
    }
    return {
      documentType: type,
      label: `Continue ${meta.title}`,
    };
  }
  // All complete — still allow regenerating the last stage.
  const last = DOCUMENT_ORDER[DOCUMENT_ORDER.length - 1]!;
  return {
    documentType: last.type as ScriptAiDocumentType,
    label: `Regenerate ${last.title}`,
  };
}

export function ScriptAiPipelinePanel({
  contents,
  activeType,
  readOnly,
  onGenerate,
  onFocusDocument,
}: ScriptAiPipelinePanelProps) {
  const action = nextAction(contents);

  return (
    <div
      className="rounded-xl border border-border/70 bg-surface/40 p-4"
      data-testid="script-ai-pipeline-panel"
    >
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-brand-orange" />
        <h3 className="text-sm font-semibold text-foreground">
          AI Draft Pipeline
        </h3>
      </div>
      <p className="mb-3 text-xs text-muted-foreground">
        Guided drafting across Discovery Brief → Story Spine → Master Script.
        Drafts are never auto-applied.
      </p>

      <ol className="space-y-2">
        {DOCUMENT_ORDER.map((meta, index) => {
          const type = meta.type as ScriptAiDocumentType;
          const status = stageStatus(type, contents);
          const blocked = status === "blocked";
          const isActive = activeType === type;
          return (
            <li
              key={type}
              className={`rounded-lg border px-3 py-2 ${
                isActive
                  ? "border-brand-orange/40 bg-brand-orange/5"
                  : "border-border/60 bg-background/40"
              }`}
              data-testid={`script-ai-pipeline-stage-${type}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <button
                  type="button"
                  className="min-w-0 text-left"
                  onClick={() => onFocusDocument?.(type)}
                >
                  <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                    Stage {index + 1}
                  </span>
                  <span className="block text-sm font-medium text-foreground">
                    {meta.title}
                  </span>
                </button>
                <StatusBadge status={statusLabel(status)} />
              </div>
              <div className="mt-2 flex justify-end">
                <Button
                  type="button"
                  variant="secondary"
                  className="h-8 text-xs"
                  disabled={readOnly || blocked}
                  onClick={() => onGenerate(type)}
                  data-testid={`script-ai-pipeline-generate-${type}`}
                >
                  Generate
                </Button>
              </div>
              {blocked ? (
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Finish prior stages first.
                </p>
              ) : null}
            </li>
          );
        })}
      </ol>

      {action && !readOnly ? (
        <div className="mt-3 border-t border-border/60 pt-3">
          <p className="mb-2 text-[11px] uppercase tracking-wide text-muted-foreground">
            Next action
          </p>
          <Button
            type="button"
            className="w-full"
            onClick={() => onGenerate(action.documentType)}
            data-testid="script-ai-pipeline-next"
          >
            <Sparkles className="h-4 w-4" />
            {action.label}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
