"use client";

import { memo } from "react";

import { CompletionBadge } from "@/components/knowledge-packs/completion-badge";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import {
  documentCompletionState,
  isDocumentComplete,
} from "@/lib/scripts/metrics";
import { cn } from "@/lib/utils";

type ScriptDocumentNavigatorProps = {
  contents: Record<string, string>;
  activeType: string;
  onNavigate: (type: string) => void;
};

export const ScriptDocumentNavigator = memo(function ScriptDocumentNavigator({
  contents,
  activeType,
  onNavigate,
}: ScriptDocumentNavigatorProps) {
  return (
    <nav aria-label="Script documents" className="space-y-1">
      {DOCUMENT_ORDER.map((meta, index) => {
        const content = contents[meta.type] ?? "";
        const complete = isDocumentComplete(content, meta);
        const state = documentCompletionState(content, meta.type);
        const active = activeType === meta.type;
        return (
          <button
            key={meta.type}
            type="button"
            onClick={() => onNavigate(meta.type)}
            className={cn(
              "flex w-full items-start gap-2 rounded-lg px-3 py-2.5 text-left transition",
              active
                ? "bg-surface-elevated text-foreground ring-1 ring-border"
                : "text-muted-foreground hover:bg-surface-hover hover:text-foreground",
            )}
            aria-current={active ? "true" : undefined}
            data-testid={`doc-nav-${meta.type}`}
          >
            <span className="mt-0.5 font-mono text-[10px] text-muted-foreground">
              {index + 1}
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground">
                  {meta.title}
                </span>
                <CompletionBadge complete={complete} />
              </span>
              <span className="mt-0.5 block text-[11px] capitalize text-muted-foreground">
                {state}
              </span>
            </span>
          </button>
        );
      })}
    </nav>
  );
});
