"use client";

import { memo } from "react";

import { CompletionBadge } from "@/components/knowledge-packs/completion-badge";
import { isSectionComplete } from "@/lib/knowledge-packs/metrics";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { cn } from "@/lib/utils";

type SectionNavigatorProps = {
  sections: SectionMeta[];
  contents: Record<string, string>;
  activeKey: string;
  onNavigate: (key: string) => void;
  className?: string;
};

export const SectionNavigator = memo(function SectionNavigator({
  sections,
  contents,
  activeKey,
  onNavigate,
  className,
}: SectionNavigatorProps) {
  return (
    <nav
      aria-label="Knowledge Pack sections"
      className={cn("flex flex-col gap-0.5", className)}
    >
      {sections.map((section) => {
        const active = section.key === activeKey;
        const complete = isSectionComplete(contents[section.key] ?? "");
        return (
          <button
            key={section.key}
            type="button"
            onClick={() => onNavigate(section.key)}
            aria-current={active ? "true" : undefined}
            className={cn(
              "flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm transition",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/50",
              active
                ? "bg-brand-orange/12 text-foreground"
                : "text-muted-foreground hover:bg-surface-hover hover:text-foreground",
            )}
          >
            <CompletionBadge complete={complete} />
            <span className="truncate">{section.title}</span>
          </button>
        );
      })}
    </nav>
  );
});
