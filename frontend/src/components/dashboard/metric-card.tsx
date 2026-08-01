import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: number | string;
  hint?: string;
  icon: LucideIcon;
  accent?: "brand" | "info" | "success" | "warning";
  className?: string;
  isDemo?: boolean;
};

const accentMap = {
  brand: "text-brand-orange bg-brand-orange/10 border-brand-orange/25",
  info: "text-info bg-info/10 border-info/25",
  success: "text-success bg-success/10 border-success/25",
  warning: "text-warning bg-warning/10 border-warning/25",
};

export function MetricCard({
  label,
  value,
  hint,
  icon: Icon,
  accent = "brand",
  className,
  isDemo = false,
}: MetricCardProps) {
  return (
    <article
      className={cn(
        "panel group flex min-w-0 items-start justify-between gap-3 p-4 transition hover:border-border-strong hover:bg-surface-elevated",
        className,
      )}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          {isDemo ? (
            <span className="rounded border border-border px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-muted-foreground">
              Demo
            </span>
          ) : null}
        </div>
        <p className="mt-2 text-2xl font-semibold tracking-tight tabular-nums text-foreground sm:text-3xl">
          {value}
        </p>
        {hint ? (
          <p className="mt-1 truncate text-xs text-muted-foreground">{hint}</p>
        ) : null}
      </div>
      <span
        className={cn(
          "inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border",
          accentMap[accent],
        )}
      >
        <Icon className="h-5 w-5" aria-hidden />
      </span>
    </article>
  );
}
