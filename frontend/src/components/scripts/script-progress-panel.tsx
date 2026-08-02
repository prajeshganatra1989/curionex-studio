"use client";

import { memo, useMemo } from "react";

import { CompletionBadge } from "@/components/knowledge-packs/completion-badge";
import { NarrationEstimate } from "@/components/scripts/narration-estimate";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import {
  completedDocumentCount,
  countWords,
  isDocumentComplete,
  totalCharacters,
  totalWords,
  workspaceCompletionPercent,
} from "@/lib/scripts/metrics";

type ScriptProgressPanelProps = {
  contents: Record<string, string>;
};

export const ScriptProgressPanel = memo(function ScriptProgressPanel({
  contents,
}: ScriptProgressPanelProps) {
  const stats = useMemo(() => {
    const words = totalWords(contents);
    const chars = totalCharacters(contents);
    const completed = completedDocumentCount(contents);
    const percent = workspaceCompletionPercent(contents);
    const masterWords = countWords(contents.master_script ?? "");
    return { words, chars, completed, percent, masterWords };
  }, [contents]);

  return (
    <aside
      className="space-y-5 rounded-xl border border-border/70 bg-surface/60 p-4"
      data-testid="script-progress-panel"
    >
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Progress
        </p>
        <p className="mt-2 text-3xl font-semibold tabular-nums text-foreground">
          {stats.percent}%
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {stats.completed} of {DOCUMENT_ORDER.length} documents structurally
          complete. Measures structure, not editorial quality.
        </p>
      </div>

      <ul className="space-y-2">
        {DOCUMENT_ORDER.map((meta) => {
          const complete = isDocumentComplete(
            contents[meta.type] ?? "",
            meta,
          );
          return (
            <li
              key={meta.type}
              className="flex items-center justify-between gap-2 text-sm"
            >
              <span className="text-muted-foreground">{meta.title}</span>
              <CompletionBadge complete={complete} />
            </li>
          );
        })}
      </ul>

      <dl className="space-y-2 border-t border-border/70 pt-4 text-sm">
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Total words</dt>
          <dd className="tabular-nums text-foreground">
            {stats.words.toLocaleString()}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Total characters</dt>
          <dd className="tabular-nums text-foreground">
            {stats.chars.toLocaleString()}
          </dd>
        </div>
        <div className="pt-1">
          <NarrationEstimate text={contents.master_script ?? ""} />
        </div>
      </dl>
    </aside>
  );
});
