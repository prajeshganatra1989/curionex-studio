"use client";

import { useEffect, useRef } from "react";

import { countCharacters } from "@/lib/knowledge-packs/metrics";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { formatRelativeTime, cn } from "@/lib/utils";

type SectionEditorProps = {
  meta: SectionMeta;
  content: string;
  savedAt: string | null;
  dirty: boolean;
  error?: string | null;
  onChange: (value: string) => void;
  onRetry?: () => void;
};

export function SectionEditor({
  meta,
  content,
  savedAt,
  dirty,
  error,
  onChange,
  onRetry,
}: SectionEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chars = countCharacters(content);
  const empty = content.trim().length === 0;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, 220)}px`;
  }, [content]);

  return (
    <section
      id={`section-${meta.key}`}
      data-section-key={meta.key}
      aria-labelledby={`heading-${meta.key}`}
      className="scroll-mt-28 border-b border-border py-10 last:border-b-0"
    >
      <header className="mb-4">
        <h2
          id={`heading-${meta.key}`}
          className="text-2xl font-semibold tracking-tight text-foreground"
        >
          {meta.title}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{meta.description}</p>
      </header>

      {empty ? (
        <p className="mb-3 rounded-lg border border-dashed border-border bg-surface/40 px-3 py-2 text-sm text-muted-foreground">
          {meta.guidance}
        </p>
      ) : null}

      <label className="sr-only" htmlFor={`editor-${meta.key}`}>
        {meta.title} content
      </label>
      <textarea
        ref={textareaRef}
        id={`editor-${meta.key}`}
        value={content}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        autoCorrect="off"
        autoCapitalize="off"
        placeholder={meta.guidance}
        className={cn(
          "min-h-[220px] w-full resize-y rounded-xl border border-border bg-surface px-4 py-4 text-base leading-7 text-foreground",
          "placeholder:text-muted-foreground/70",
          "focus-visible:border-brand-orange/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/30",
          "shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]",
          dirty && "border-brand-amber/40",
        )}
      />

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
        <span className="tabular-nums">
          {chars.toLocaleString()} character{chars === 1 ? "" : "s"}
        </span>
        <span>
          {dirty
            ? "Unsaved changes"
            : savedAt
              ? `Last saved ${formatRelativeTime(savedAt)}`
              : "Not saved yet"}
        </span>
      </div>

      {error ? (
        <div
          className="mt-3 flex flex-wrap items-center gap-3 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger"
          role="alert"
        >
          <span className="flex-1">{error}</span>
          {onRetry ? (
            <button
              type="button"
              className="text-sm font-medium text-brand-orange underline"
              onClick={onRetry}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
