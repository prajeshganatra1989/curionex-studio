"use client";

import { memo, useEffect, useRef } from "react";

import { CharacterCounter } from "@/components/knowledge-packs/character-counter";
import { WordCounter } from "@/components/knowledge-packs/word-counter";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { cn, formatRelativeTime } from "@/lib/utils";

type KnowledgePackSectionProps = {
  meta: SectionMeta;
  content: string;
  savedAt: string | null;
  dirty: boolean;
  error?: string | null;
  onChange: (value: string) => void;
  onRetry?: () => void;
};

export const KnowledgePackSection = memo(function KnowledgePackSection({
  meta,
  content,
  savedAt,
  dirty,
  error,
  onChange,
  onRetry,
}: KnowledgePackSectionProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const empty = content.trim().length === 0;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, 280)}px`;
  }, [content]);

  return (
    <section
      id={`section-${meta.key}`}
      data-section-key={meta.key}
      aria-labelledby={`heading-${meta.key}`}
      className="scroll-mt-32 py-14 first:pt-6 last:pb-24"
    >
      <header className="mb-6 max-w-3xl">
        <h2
          id={`heading-${meta.key}`}
          className="text-[1.75rem] font-semibold tracking-tight text-foreground"
        >
          {meta.title}
        </h2>
        <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
          {meta.description}
        </p>
      </header>

      {empty ? (
        <p className="mb-4 max-w-3xl text-sm leading-relaxed text-muted-foreground/90">
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
          "min-h-[280px] w-full resize-y rounded-2xl border border-border/80 bg-surface/60 px-5 py-5",
          "text-[17px] leading-8 text-foreground tracking-[0.01em]",
          "placeholder:text-muted-foreground/55",
          "focus-visible:border-brand-orange/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/25",
          "transition-[border-color,box-shadow] duration-200",
          dirty && "border-brand-amber/45",
        )}
      />

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
        <div className="flex flex-wrap gap-3 tabular-nums">
          <WordCounter text={content} />
          <span aria-hidden>·</span>
          <CharacterCounter text={content} />
        </div>
        <span>
          {dirty
            ? "Unsaved changes"
            : savedAt
              ? `Saved ${formatRelativeTime(savedAt)}`
              : "Not saved yet"}
        </span>
      </div>

      {error ? (
        <div
          className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
          role="alert"
        >
          <span className="flex-1">{error}</span>
          {onRetry ? (
            <button
              type="button"
              className="font-medium text-brand-orange underline"
              onClick={onRetry}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
});
