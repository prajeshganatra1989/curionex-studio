import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionPanelProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function SectionPanel({
  title,
  description,
  action,
  children,
  className,
}: SectionPanelProps) {
  return (
    <section className={cn("panel flex flex-col", className)}>
      <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {description ? (
            <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {action}
      </header>
      <div className="flex-1 p-2 sm:p-3">{children}</div>
    </section>
  );
}
