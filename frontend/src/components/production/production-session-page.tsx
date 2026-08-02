"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Library, RefreshCw } from "lucide-react";

import { PageContainer } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { ApiError } from "@/lib/api/client";
import { useProductionSession } from "@/lib/production/hooks";
import type {
  ProductionSessionCurrent,
  ProductionSessionTimelineStep,
} from "@/lib/production/types";

function SessionSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true" data-testid="session-loading">
      <LoadingSkeleton className="h-28" />
      <LoadingSkeleton className="h-64" />
      <LoadingSkeleton className="h-40" />
    </div>
  );
}

function ProgressBar({ percent }: { percent: number }) {
  const width = Math.max(0, Math.min(100, percent));
  return (
    <div
      className="h-3 w-full overflow-hidden rounded-full bg-surface-elevated"
      role="progressbar"
      aria-valuenow={Math.round(width)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full bg-brand-orange transition-[width]"
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function Timeline({ steps }: { steps: ProductionSessionTimelineStep[] }) {
  return (
    <ol className="space-y-2" data-testid="session-timeline">
      {steps.map((step) => {
        const color =
          step.status === "complete"
            ? "border-emerald-500/50 text-emerald-400"
            : step.status === "current"
              ? "border-brand-amber/60 text-brand-amber"
              : "border-border text-muted-foreground";
        return (
          <li
            key={step.key}
            className={`flex items-center gap-3 rounded-lg border px-3 py-2 text-sm ${color}`}
            data-status={step.status}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                step.status === "complete"
                  ? "bg-emerald-400"
                  : step.status === "current"
                    ? "bg-brand-amber"
                    : "bg-muted-foreground/40"
              }`}
              aria-hidden
            />
            <span className="font-medium">{step.label}</span>
            <span className="ml-auto text-[11px] uppercase tracking-wide opacity-80">
              {step.status}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function Sidebar({ current }: { current: ProductionSessionCurrent }) {
  const sidebar = current.sidebar;
  if (!sidebar) return null;
  return (
    <aside
      className="space-y-3 rounded-xl border border-border bg-surface p-4"
      data-testid="session-sidebar"
    >
      <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Context
      </h2>
      <dl className="space-y-3 text-sm">
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Wave</dt>
          <dd className="font-medium tabular-nums">{sidebar.wave ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Priority</dt>
          <dd className="font-medium">{sidebar.priority ?? "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Est. remaining</dt>
          <dd className="font-medium tabular-nums">
            {sidebar.estimated_remaining_minutes} min
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Quality</dt>
          <dd className="font-medium tabular-nums">
            {sidebar.quality_score ?? "—"}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Approval</dt>
          <dd className="font-medium capitalize">
            {(sidebar.approval_status ?? "—").replaceAll("_", " ")}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Knowledge Pack</dt>
          <dd className="font-medium capitalize">{sidebar.knowledge_pack_status}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Version</dt>
          <dd className="font-medium capitalize">
            {(sidebar.version_status ?? "—").replaceAll("_", " ")}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-muted-foreground">Reviewer</dt>
          <dd className="font-medium">{sidebar.reviewer ?? "—"}</dd>
        </div>
      </dl>
    </aside>
  );
}

export function ProductionSessionPage() {
  const router = useRouter();
  const { data, isLoading, isError, error, refetch, isFetching } =
    useProductionSession();

  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  if (isLoading && !data) {
    return (
      <PageContainer>
        <SessionSkeleton />
      </PageContainer>
    );
  }

  if (restricted) {
    return (
      <PageContainer>
        <EmptyState
          title="Session restricted"
          description="You need production.view to open the Production Session."
        />
      </PageContainer>
    );
  }

  if ((isError && !data) || !data) {
    return (
      <PageContainer>
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load session."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void refetch()}
            >
              Try again
            </button>
          }
        />
      </PageContainer>
    );
  }

  const { today, progress, current, upcoming, previous_completed, warnings, empty } =
    data;

  return (
    <PageContainer>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-amber">
            Production Session
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-foreground">
            Today&apos;s Goal
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {today.completed} / {today.goal} approved scripts
            {today.estimated_finish ? ` · ${today.estimated_finish}` : ""}
            {` · Streak ${today.current_streak}`}
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-surface-hover disabled:opacity-60"
          disabled={isFetching}
          onClick={() => void refetch()}
          data-testid="session-refresh"
        >
          <RefreshCw
            className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
            aria-hidden
          />
          Refresh
        </button>
      </div>

      <section
        className="mb-8 rounded-2xl border border-border bg-surface p-5"
        data-testid="session-counter"
      >
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Approved Scripts
            </p>
            <p className="mt-1 text-3xl font-semibold tabular-nums">
              {progress.approved_total} / {progress.approved_target}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-semibold tabular-nums text-brand-amber">
              {progress.completion_percent}%
            </p>
            <p className="text-xs text-muted-foreground">
              Remaining {progress.remaining}
            </p>
          </div>
        </div>
        <div className="mt-4">
          <ProgressBar percent={progress.completion_percent} />
        </div>
      </section>

      {warnings.length > 0 ? (
        <div
          className="mb-6 rounded-xl border border-brand-amber/40 bg-brand-amber/10 px-4 py-3 text-sm text-brand-amber"
          data-testid="session-warnings"
        >
          <ul className="list-disc space-y-1 pl-4">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {empty || !current ? (
        <div
          className="rounded-2xl border border-border bg-surface px-6 py-16 text-center"
          data-testid="session-empty"
        >
          <p className="text-4xl" aria-hidden>
            🎉
          </p>
          <h2 className="mt-4 text-2xl font-semibold">All production work completed</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            Choose another Editorial Topic to start the next Shorts production.
          </p>
          <Link
            href={data.browse_topics_url}
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-orange px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90"
            data-testid="browse-editorial-library"
          >
            <Library className="h-4 w-4" aria-hidden />
            Browse Editorial Library
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
          <div className="space-y-6">
            <section
              className="rounded-2xl border border-border bg-surface p-5"
              data-testid="session-current"
            >
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Current Production
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                {current.topic_title}
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Current Stage
              </p>
              <p className="text-lg font-medium text-brand-amber">
                {current.stage_label}
              </p>
              <p className="mt-4 text-sm text-muted-foreground">Next Action</p>
              <p className="text-base font-medium">{current.next_action.label}</p>
              <div className="mt-6">
                <Button
                  type="button"
                  className="h-11 px-5 text-sm font-semibold"
                  data-testid="session-continue"
                  disabled={!current.continue_url}
                  onClick={() => {
                    if (current.continue_url) {
                      router.push(current.continue_url);
                    }
                  }}
                >
                  Continue
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Button>
              </div>
            </section>

            <section className="rounded-2xl border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold">Production Timeline</h3>
              <Timeline steps={current.timeline} />
            </section>

            {previous_completed ? (
              <p className="text-sm text-muted-foreground" data-testid="session-previous">
                Previously completed:{" "}
                <span className="text-foreground">{previous_completed.topic_title}</span>
              </p>
            ) : null}

            <section
              className="rounded-2xl border border-border bg-surface p-5"
              data-testid="session-queue"
            >
              <h3 className="mb-3 text-sm font-semibold">Upcoming queue</h3>
              {upcoming.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No additional productions queued.
                </p>
              ) : (
                <ul className="space-y-3">
                  {upcoming.map((item) => (
                    <li
                      key={`${item.project_id}-${item.script_id ?? "project"}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/70 px-3 py-3"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium">{item.topic_title}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.stage_label}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="secondary"
                        className="h-8 px-3 text-xs"
                        disabled={!item.continue_url}
                        onClick={() => {
                          if (item.continue_url) router.push(item.continue_url);
                        }}
                      >
                        Continue
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <Sidebar current={current} />
        </div>
      )}
    </PageContainer>
  );
}
