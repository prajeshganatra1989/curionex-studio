import type { DailyGoal } from "@/lib/dashboard/types";
import { cn } from "@/lib/utils";

type DailyGoalCardProps = {
  goal: DailyGoal;
};

export function DailyGoalCard({ goal }: DailyGoalCardProps) {
  const pct = Math.min(
    100,
    Math.round((goal.completed / Math.max(goal.target, 1)) * 100),
  );
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <article className="panel relative h-full overflow-hidden p-5">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(232,114,12,0.14),transparent_55%)]"
      />
      <div className="relative flex h-full items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              Today&apos;s Goal
            </h2>
            {goal.isDemo ? (
              <span className="rounded-md border border-border bg-surface-elevated px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                Demo
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-lg font-semibold text-foreground">
            <span className="tabular-nums">
              {goal.completed} / {goal.target}
            </span>
            {goal.isDemo ? " Videos" : " Approved"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{goal.label}</p>
        </div>
        <div
          className="relative h-24 w-24 shrink-0"
          role="img"
          aria-label={`${pct}% of daily goal complete`}
        >
          <svg className="h-full w-full -rotate-90" viewBox="0 0 96 96">
            <circle
              cx="48"
              cy="48"
              r={radius}
              fill="none"
              stroke="var(--border)"
              strokeWidth="8"
            />
            <circle
              cx="48"
              cy="48"
              r={radius}
              fill="none"
              stroke="url(#goalGradient)"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className={cn(
                "transition-[stroke-dashoffset] duration-700 ease-out",
              )}
            />
            <defs>
              <linearGradient id="goalGradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="var(--brand-yellow)" />
                <stop offset="100%" stopColor="var(--brand-orange)" />
              </linearGradient>
            </defs>
          </svg>
          <span className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-sm font-semibold tabular-nums">{pct}%</span>
            <span className="text-[10px] text-muted-foreground">Completed</span>
          </span>
        </div>
      </div>
    </article>
  );
}
