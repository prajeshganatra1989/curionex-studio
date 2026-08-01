import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent?: "brand" | "info" | "success" | "warning";
  className?: string;
};

const accentMap = {
  brand: "text-brand-orange bg-brand-orange/10 border-brand-orange/20",
  info: "text-info bg-info/10 border-info/20",
  success: "text-success bg-success/10 border-success/20",
  warning: "text-warning bg-warning/10 border-warning/20",
};

export function MetricCard({
  label,
  value,
  icon: Icon,
  accent = "brand",
  className,
}: MetricCardProps) {
  return (
    <article
      className={cn(
        "panel group flex items-start justify-between gap-3 p-4 transition hover:border-border-strong hover:bg-surface-elevated",
        className,
      )}
    >
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight tabular-nums text-foreground">
          {value}
        </p>
      </div>
      <span
        className={cn(
          "inline-flex h-10 w-10 items-center justify-center rounded-lg border",
          accentMap[accent],
        )}
      >
        <Icon className="h-5 w-5" aria-hidden />
      </span>
    </article>
  );
}
