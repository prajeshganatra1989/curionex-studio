"use client";

import { memo, useMemo } from "react";

import { CompletionBadge } from "@/components/knowledge-packs/completion-badge";
import {
  completionPercent,
  countCharacters,
  countWords,
  formatReadingTime,
  isSectionComplete,
} from "@/lib/knowledge-packs/metrics";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { cn } from "@/lib/utils";

type ProgressSidebarProps = {
  sections: SectionMeta[];
  contents: Record<string, string>;
  className?: string;
};

export const ProgressSidebar = memo(function ProgressSidebar({
  sections,
  contents,
  className,
}: ProgressSidebarProps) {
  const stats = useMemo(() => {
    const values = sections.map((s) => contents[s.key] ?? "");
    const words = values.reduce((sum, text) => sum + countWords(text), 0);
    const chars = values.reduce((sum, text) => sum + countCharacters(text), 0);
    return {
      percent: completionPercent(values),
      words,
      chars,
      reading: formatReadingTime(words),
      completeCount: values.filter(isSectionComplete).length,
    };
  }, [sections, contents]);

  return (
    <aside
      aria-label="Writing progress"
      className={cn(
        "rounded-2xl border border-border bg-surface/80 p-5 backdrop-blur",
        className,
      )}
    >
      <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        Progress
      </h2>

      <div className="mt-5">
        <div className="flex items-end justify-between gap-2">
          <p className="text-4xl font-semibold tracking-tight tabular-nums text-foreground">
            {stats.percent}%
          </p>
          <p className="pb-1 text-xs text-muted-foreground">Completion</p>
        </div>
        <div
          className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-elevated"
          role="progressbar"
          aria-valuenow={stats.percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Section completion"
        >
          <div
            className="h-full rounded-full bg-brand-gradient transition-[width] duration-300"
            style={{ width: `${stats.percent}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {stats.completeCount} of {sections.length} sections started
        </p>
      </div>

      <ul className="mt-6 space-y-2.5">
        {sections.map((section) => {
          const done = isSectionComplete(contents[section.key] ?? "");
          return (
            <li
              key={section.key}
              className="flex items-center justify-between gap-2 text-sm"
            >
              <span className="truncate text-muted-foreground">
                {section.title}
              </span>
              <CompletionBadge complete={done} />
            </li>
          );
        })}
      </ul>

      <dl className="mt-6 space-y-3 border-t border-border pt-5 text-sm">
        <div className="flex items-center justify-between gap-2">
          <dt className="text-muted-foreground">Word count</dt>
          <dd className="tabular-nums font-medium text-foreground">
            {stats.words.toLocaleString()}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-muted-foreground">Characters</dt>
          <dd className="tabular-nums font-medium text-foreground">
            {stats.chars.toLocaleString()}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-muted-foreground">Reading time</dt>
          <dd className="tabular-nums font-medium text-foreground">
            {stats.reading}
          </dd>
        </div>
      </dl>
    </aside>
  );
});
