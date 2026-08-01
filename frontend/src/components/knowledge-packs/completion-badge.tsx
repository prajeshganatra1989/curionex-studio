"use client";

import { memo } from "react";

import { cn } from "@/lib/utils";
import { isSectionComplete } from "@/lib/knowledge-packs/metrics";

type CompletionBadgeProps = {
  complete: boolean;
  className?: string;
  label?: string;
};

export const CompletionBadge = memo(function CompletionBadge({
  complete,
  className,
  label,
}: CompletionBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-full text-xs font-medium",
        complete
          ? "bg-success/15 text-success"
          : "bg-surface-elevated text-muted-foreground",
        className,
      )}
      aria-label={label ?? (complete ? "Complete" : "Empty")}
    >
      {complete ? "✔" : "○"}
    </span>
  );
});

export function sectionCompleteFromContent(content: string): boolean {
  return isSectionComplete(content);
}
