"use client";

import { memo, useEffect, useRef } from "react";

import { CharacterCounter } from "@/components/knowledge-packs/character-counter";
import { WordCounter } from "@/components/knowledge-packs/word-counter";
import { NarrationEstimate } from "@/components/scripts/narration-estimate";
import { Button } from "@/components/ui/button";
import type { DocumentMeta } from "@/lib/scripts/documents";
import { formatRelativeTime } from "@/lib/utils";

type ScriptDocumentEditorProps = {
  meta: DocumentMeta;
  content: string;
  dirty: boolean;
  savedAt: string | null;
  error: string | null;
  readOnly?: boolean;
  onChange: (value: string) => void;
  onRetry: () => void;
  active?: boolean;
};

export const ScriptDocumentEditor = memo(function ScriptDocumentEditor({
  meta,
  content,
  dirty,
  savedAt,
  error,
  readOnly,
  onChange,
  onRetry,
  active,
}: ScriptDocumentEditorProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, 280)}px`;
  }, [content]);

  useEffect(() => {
    if (active) {
      ref.current?.focus({ preventScroll: true });
    }
  }, [active]);

  return (
    <section
      id={`document-${meta.type}`}
      data-document-type={meta.type}
      aria-labelledby={`document-title-${meta.type}`}
      className="scroll-mt-28 py-8 first:pt-2"
    >
      <header className="mb-4">
        <h2
          id={`document-title-${meta.type}`}
          className="text-xl font-semibold tracking-tight text-foreground"
        >
          {meta.title}
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          {meta.description}
        </p>
      </header>

      <label className="sr-only" htmlFor={`editor-${meta.type}`}>
        {meta.title} content
      </label>
      <textarea
        ref={ref}
        id={`editor-${meta.type}`}
        value={content}
        readOnly={readOnly}
        onChange={(e) => onChange(e.target.value)}
        placeholder={meta.guidance}
        spellCheck
        className="w-full resize-none rounded-xl border border-border/80 bg-background/60 px-4 py-4 text-base leading-relaxed text-foreground outline-none transition placeholder:text-muted-foreground/70 focus-visible:border-brand-amber/60 focus-visible:ring-2 focus-visible:ring-brand-amber/20 disabled:opacity-70"
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `error-${meta.type}` : undefined}
        data-testid={`editor-${meta.type}`}
      />

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <WordCounter text={content} />
        <CharacterCounter text={content} />
        {meta.type === "master_script" ? (
          <NarrationEstimate text={content} />
        ) : null}
        <span aria-live="polite">
          {dirty
            ? "Unsaved"
            : savedAt
              ? `Saved ${formatRelativeTime(savedAt)}`
              : "Not saved yet"}
        </span>
      </div>

      {error ? (
        <div
          id={`error-${meta.type}`}
          className="mt-3 flex flex-wrap items-center gap-3 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger"
          role="alert"
        >
          <span>Save failed: {error}</span>
          <Button type="button" variant="secondary" className="h-8" onClick={onRetry}>
            Retry
          </Button>
        </div>
      ) : null}
    </section>
  );
});
