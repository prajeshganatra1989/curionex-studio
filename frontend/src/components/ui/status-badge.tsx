import { cn } from "@/lib/utils";
import { statusLabel, statusTone } from "@/lib/status";

const toneClasses: Record<ReturnType<typeof statusTone>, string> = {
  success:
    "bg-success/15 text-success border-success/30",
  warning:
    "bg-warning/15 text-warning border-warning/30",
  danger: "bg-danger/15 text-danger border-danger/30",
  info: "bg-info/15 text-info border-info/30",
  muted:
    "bg-muted-foreground/10 text-muted-foreground border-border",
  neutral:
    "bg-surface-hover text-foreground border-border",
};

type StatusBadgeProps = {
  status: string;
  className?: string;
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const tone = statusTone(status);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
        toneClasses[tone],
        className,
      )}
    >
      {statusLabel(status)}
    </span>
  );
}
