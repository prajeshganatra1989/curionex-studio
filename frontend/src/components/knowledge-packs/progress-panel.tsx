"use client";

import {
  completionPercent,
  countWords,
  formatReadingTime,
  isSectionComplete,
} from "@/lib/knowledge-packs/metrics";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { cn } from "@/lib/utils";

type ProgressPanelProps = {
  sections: SectionMeta[];
  contents: Record<string, string>;
  className?: string;
};

export function ProgressPanel({
  sections,
  contents,
  className,
}: ProgressPanelProps) {
  const values = sections.map((s) => contents[s.key] ?? "");
  const percent = completionPercent(values);
  const totalWords = values.reduce((sum, text) => sum + countWords(text), 0);
  const reading = formatReadingTime(totalWords);
  const completeCount = values.filter(isSectionComplete).length;

  return (
    <aside
      aria-label="Writing progress"
      className={cn(
        "rounded-xl border border-border bg-surface p-4",
        className,
      )}
    >
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Progress
      </h2>

      <div className="mt-4">
        <div className="flex items-end justify-between gap-2">
          <p className="text-3xl font-semibold tabular-nums text-foreground">
            {percent}%
          </p>
          <p className="text-xs text-muted-foreground">Completion</p>
        </div>
        <div
          className="mt-2 h-2 overflow-hidden rounded-full bg-surface-elevated"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Section completion"
        >
          <div
            className="h-full rounded-full bg-brand-gradient transition-[width] duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {completeCount} of {sections.length} sections started
        </p>
      </div>

      <ul className="mt-5 space-y-2">
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
              <span
                className={cn(
                  "text-xs font-medium",
                  done ? "text-success" : "text-muted-foreground",
                )}
              >
                {done ? "Done" : "Empty"}
              </span>
            </li>
          );
        })}
      </ul>

      <dl className="mt-6 space-y-3 border-t border-border pt-4 text-sm">
        <div className="flex items-center justify-between gap-2">
          <dt className="text-muted-foreground">Word count</dt>
          <dd className="tabular-nums font-medium text-foreground">
            {totalWords.toLocaleString()}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-muted-foreground">Reading time</dt>
          <dd className="tabular-nums font-medium text-foreground">{reading}</dd>
        </div>
      </dl>
    </aside>
  );
}
