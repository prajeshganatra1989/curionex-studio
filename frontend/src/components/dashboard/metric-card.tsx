import type { LucideIcon } from "lucide-react";

import type { MetricAvailability } from "@/lib/dashboard/types";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: number | null;
  availability: MetricAvailability;
  hint?: string;
  icon: LucideIcon;
  accent?: "brand" | "info" | "success" | "warning";
  className?: string;
  /** Format a live numeric value (e.g. quality score). */
  formatValue?: (value: number) => string;
};

const accentMap = {
  brand: "text-brand-orange bg-brand-orange/10 border-brand-orange/25",
  info: "text-info bg-info/10 border-info/25",
  success: "text-success bg-success/10 border-success/25",
  warning: "text-warning bg-warning/10 border-warning/25",
};

function displayValue(
  value: number | null,
  availability: MetricAvailability,
  formatValue?: (value: number) => string,
): string {
  if (availability === "restricted") return "Restricted";
  if (availability === "unavailable") return "Unavailable";
  if (value == null) return "—";
  return formatValue ? formatValue(value) : String(value);
}

export function MetricCard({
  label,
  value,
  availability,
  hint,
  icon: Icon,
  accent = "brand",
  className,
  formatValue,
}: MetricCardProps) {
  const shown = displayValue(value, availability, formatValue);
  const isNumericLive = availability === "live" && value != null;

  return (
    <article
      className={cn(
        "panel group flex min-w-0 items-start justify-between gap-3 p-4 transition hover:border-border-strong hover:bg-surface-elevated",
        className,
      )}
      data-availability={availability}
    >
      <div className="min-w-0">
        <p className="truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p
          className={cn(
            "mt-2 font-semibold tracking-tight text-foreground",
            isNumericLive
              ? "text-2xl tabular-nums sm:text-3xl"
              : "text-base sm:text-lg",
          )}
        >
          {shown}
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
