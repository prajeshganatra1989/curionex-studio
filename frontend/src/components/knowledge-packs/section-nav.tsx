"use client";

import { cn } from "@/lib/utils";
import type { SectionMeta } from "@/lib/knowledge-packs/sections";
import { isSectionComplete } from "@/lib/knowledge-packs/metrics";

type SectionNavProps = {
  sections: SectionMeta[];
  contents: Record<string, string>;
  activeKey: string;
  onNavigate: (key: string) => void;
  orientation?: "vertical" | "horizontal";
  className?: string;
};

export function SectionNav({
  sections,
  contents,
  activeKey,
  onNavigate,
  orientation = "vertical",
  className,
}: SectionNavProps) {
  const horizontal = orientation === "horizontal";

  return (
    <nav
      aria-label={
        horizontal
          ? "Knowledge Pack sections (mobile)"
          : "Knowledge Pack sections"
      }
      className={cn(
        horizontal
          ? "flex gap-1 overflow-x-auto pb-1"
          : "flex flex-col gap-1",
        className,
      )}
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
              "rounded-lg px-3 py-2 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/50",
              horizontal ? "shrink-0 whitespace-nowrap" : "w-full",
              active
                ? "bg-brand-orange/15 text-foreground"
                : "text-muted-foreground hover:bg-surface-hover hover:text-foreground",
            )}
          >
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  "h-1.5 w-1.5 shrink-0 rounded-full",
                  complete ? "bg-success" : "bg-border-strong",
                )}
                aria-hidden
              />
              {section.title}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
