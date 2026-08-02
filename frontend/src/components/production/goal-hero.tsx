"use client";

import { Check } from "lucide-react";

import type { ProductionGoalsSummary } from "@/lib/production/types";
import {
  MILESTONE_THRESHOLDS,
  achievedMilestones,
} from "@/lib/production/types";
import { cn } from "@/lib/utils";

type GoalHeroProps = {
  goals: ProductionGoalsSummary;
  className?: string;
};

export function GoalHero({ goals, className }: GoalHeroProps) {
  const pct = Math.min(100, Math.max(0, goals.completion_percent));
  const milestones = achievedMilestones(goals.approved_total);
  const dailyPct = Math.min(
    100,
    Math.round(
      (goals.approved_today / Math.max(goals.daily_target, 1)) * 100,
    ),
  );
  const weeklyPct = Math.min(
    100,
    Math.round(
      (goals.approved_this_week / Math.max(goals.weekly_target, 1)) * 100,
    ),
  );

  return (
    <section
      className={cn(
        "panel relative overflow-hidden p-5 sm:p-6",
        className,
      )}
      data-testid="goal-hero"
      aria-label="Production goals"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(232,114,12,0.12),transparent_55%)]"
      />
      <div className="relative grid gap-6 lg:grid-cols-[1fr_auto]">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Approved scripts
          </p>
          <p className="mt-2 text-4xl font-semibold tracking-tight tabular-nums text-foreground sm:text-5xl">
            <span data-testid="approved-total">{goals.approved_total}</span>
            <span className="text-muted-foreground">/</span>
            <span data-testid="approved-target">{goals.approved_target}</span>
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            {goals.remaining} remaining
            {goals.projected_days_remaining != null ? (
              <>
                <span aria-hidden> · </span>
                ~{Math.ceil(goals.projected_days_remaining)} days at current pace
              </>
            ) : null}
          </p>

          <div className="mt-4">
            <div
              className="h-2.5 overflow-hidden rounded-full bg-border/80"
              role="progressbar"
              aria-valuenow={Math.round(pct)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${Math.round(pct)}% of approved script target`}
            >
              <div
                className="h-full rounded-full bg-brand-gradient transition-[width] duration-700 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="mt-1.5 text-xs tabular-nums text-muted-foreground">
              {Math.round(pct)}% complete
            </p>
          </div>

          <ul
            className="mt-4 flex flex-wrap gap-1.5"
            aria-label="Milestones"
            data-testid="milestones"
          >
            {MILESTONE_THRESHOLDS.map((threshold) => {
              const hit = milestones.includes(threshold);
              return (
                <li
                  key={threshold}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] tabular-nums",
                    hit
                      ? "border-brand-orange/35 bg-brand-orange/10 text-brand-amber"
                      : "border-border bg-surface text-muted-foreground",
                  )}
                >
                  {hit ? <Check className="h-3 w-3" aria-hidden /> : null}
                  {threshold}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:w-72 lg:grid-cols-1">
          <MiniGoal
            label="Today"
            completed={goals.approved_today}
            target={goals.daily_target}
            pct={dailyPct}
            testId="daily-goal"
          />
          <MiniGoal
            label="This week"
            completed={goals.approved_this_week}
            target={goals.weekly_target}
            pct={weeklyPct}
            testId="weekly-goal"
          />
        </div>
      </div>
    </section>
  );
}

function MiniGoal({
  label,
  completed,
  target,
  pct,
  testId,
}: {
  label: string;
  completed: number;
  target: number;
  pct: number;
  testId: string;
}) {
  return (
    <div
      className="rounded-xl border border-border/70 bg-surface/50 px-4 py-3"
      data-testid={testId}
    >
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-foreground">
        {completed} / {target}
      </p>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border/80">
        <div
          className="h-full rounded-full bg-brand-orange/80 transition-[width] duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
