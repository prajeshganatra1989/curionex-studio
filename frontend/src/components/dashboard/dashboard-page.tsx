"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  Factory,
  FilePenLine,
  FileText,
  FolderKanban,
  RefreshCw,
  Sparkles,
} from "lucide-react";

import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { DailyGoalCard } from "@/components/dashboard/daily-goal-card";
import { MetricCard } from "@/components/dashboard/metric-card";
import { PendingReviewsList } from "@/components/dashboard/pending-reviews-list";
import { RecentProjectsList } from "@/components/dashboard/recent-projects-list";
import { RecentScriptsList } from "@/components/dashboard/recent-scripts-list";
import { PageContainer } from "@/components/layout/page-header";
import { SectionPanel } from "@/components/ui/section-panel";
import { DashboardSkeleton } from "@/components/ui/loading-skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useAuth } from "@/lib/auth/auth-context";
import { getDashboardData } from "@/lib/dashboard/data";
import type { MetricAvailability, MetricValue } from "@/lib/dashboard/types";
import { productionKeys } from "@/lib/production/hooks";
import { projectKeys } from "@/lib/projects/hooks";
import { reviewKeys } from "@/lib/reviews/hooks";
import { greetingForHour } from "@/lib/utils";

export const DASHBOARD_QUERY_KEY = ["dashboard"] as const;

function ViewAllLink({ href }: { href: string }) {
  return (
    <Link
      href={href}
      className="text-xs font-medium text-brand-orange hover:underline"
    >
      View all
    </Link>
  );
}

function metricHint(metric: MetricValue, liveHint: string): string {
  if (metric.availability === "restricted") return "Permission required";
  if (metric.availability === "unavailable") return "Temporarily unavailable";
  return liveHint;
}

function panelRestricted(availability: MetricAvailability): boolean {
  return availability === "restricted";
}

function panelUnavailable(availability: MetricAvailability): boolean {
  return availability === "unavailable";
}

export function DashboardPage() {
  const { user, api, status } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: () => getDashboardData(api),
    enabled: status === "authenticated",
  });

  const hour = new Date().getHours();
  const greeting = greetingForHour(hour);
  const firstName = user?.first_name ?? "there";

  async function handleRefresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: productionKeys.overview() }),
      queryClient.invalidateQueries({ queryKey: productionKeys.queues() }),
      queryClient.invalidateQueries({ queryKey: projectKeys.all }),
      queryClient.invalidateQueries({ queryKey: reviewKeys.all }),
    ]);
    await refetch();
  }

  if ((isLoading && !data) || status === "loading") {
    return (
      <PageContainer>
        <DashboardSkeleton />
      </PageContainer>
    );
  }

  if ((isError && !data) || !data) {
    return (
      <PageContainer>
        <ErrorState
          message={
            error instanceof Error
              ? error.message
              : "Unable to load dashboard."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void handleRefresh()}
            >
              Try again
            </button>
          }
        />
      </PageContainer>
    );
  }

  const { metrics } = data;

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-stretch lg:justify-between">
        <div className="flex min-w-0 flex-1 flex-col justify-center">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            {greeting}, {firstName}!{" "}
            <span aria-hidden className="inline-block">
              👋
            </span>
          </h1>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground sm:text-base">
            Live studio snapshot — open Production Mode for the full queue.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Link
              href="/production"
              data-testid="open-production-mode"
              className="inline-flex w-fit items-center gap-2 rounded-lg border border-brand-orange/35 bg-brand-orange/10 px-3 py-2 text-sm font-medium text-brand-amber transition hover:bg-brand-orange/15"
            >
              <Factory className="h-4 w-4" aria-hidden />
              Open Production Mode
            </Link>
            <button
              type="button"
              data-testid="dashboard-refresh"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground transition hover:bg-surface-hover disabled:opacity-60"
              disabled={isFetching}
              onClick={() => void handleRefresh()}
            >
              <RefreshCw
                className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
                aria-hidden
              />
              {isFetching ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
        <div className="w-full max-w-sm shrink-0 lg:w-80">
          <DailyGoalCard goal={data.dailyGoal} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <MetricCard
          label="Projects"
          value={metrics.projects.value}
          availability={metrics.projects.availability}
          hint={metricHint(metrics.projects, "From project list")}
          icon={FolderKanban}
          accent="brand"
        />
        <MetricCard
          label="Knowledge Packs"
          value={metrics.knowledgePacks.value}
          availability={metrics.knowledgePacks.availability}
          hint={metricHint(metrics.knowledgePacks, "Production overview")}
          icon={BookOpen}
          accent="brand"
        />
        <MetricCard
          label="Scripts"
          value={metrics.scripts.value}
          availability={metrics.scripts.availability}
          hint={metricHint(metrics.scripts, "Non-archived scripts")}
          icon={FileText}
          accent="brand"
        />
        <MetricCard
          label="Draft Scripts"
          value={metrics.draftScripts.value}
          availability={metrics.draftScripts.availability}
          hint={metricHint(metrics.draftScripts, "Status = draft")}
          icon={FilePenLine}
          accent="brand"
        />
        <MetricCard
          label="Needs Revision"
          value={metrics.needingRevision.value}
          availability={metrics.needingRevision.availability}
          hint={metricHint(metrics.needingRevision, "Production quality")}
          icon={AlertTriangle}
          accent="warning"
        />
        <MetricCard
          label="Pending Reviews"
          value={metrics.pendingReviews.value}
          availability={metrics.pendingReviews.availability}
          hint={metricHint(
            metrics.pendingReviews,
            "Pending human review stage",
          )}
          icon={ClipboardList}
          accent="warning"
        />
        <MetricCard
          label="Approved Scripts"
          value={metrics.approvedScripts.value}
          availability={metrics.approvedScripts.availability}
          hint={metricHint(metrics.approvedScripts, "Toward production goal")}
          icon={CheckCircle2}
          accent="success"
        />
        <MetricCard
          label="AI Jobs Running"
          value={metrics.aiRunning.value}
          availability={metrics.aiRunning.availability}
          hint={metricHint(metrics.aiRunning, "Live AI jobs")}
          icon={Sparkles}
          accent="info"
        />
      </div>

      {metrics.aiRunning.availability === "live" ||
      metrics.aiFailed.availability === "live" ||
      metrics.averageQualityScore.availability === "live" ? (
        <p
          className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground"
          data-testid="ai-quality-hint"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden />
          {metrics.aiFailed.availability === "live" ? (
            <>
              AI failed:{" "}
              <span className="tabular-nums text-foreground">
                {metrics.aiFailed.value}
              </span>
              <span aria-hidden>·</span>
            </>
          ) : null}
          {metrics.averageQualityScore.availability === "live" ? (
            <>
              Avg quality:{" "}
              <span className="tabular-nums text-foreground">
                {metrics.averageQualityScore.value == null
                  ? "—"
                  : metrics.averageQualityScore.value}
              </span>
              <span aria-hidden>·</span>
            </>
          ) : null}
          {metrics.staleQualityReviews.availability === "live" ? (
            <>
              Stale reviews:{" "}
              <span className="tabular-nums text-foreground">
                {metrics.staleQualityReviews.value}
              </span>
              <span aria-hidden>·</span>
            </>
          ) : null}
          Quality scores are advisory — never treated as Approved.
        </p>
      ) : null}

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <SectionPanel
          title="Recent Projects"
          action={<ViewAllLink href="/projects" />}
        >
          <RecentProjectsList
            projects={data.recentProjects}
            unavailable={panelUnavailable(data.recentProjectsAvailability)}
            restricted={panelRestricted(data.recentProjectsAvailability)}
          />
        </SectionPanel>
        <SectionPanel
          title="Recent Scripts"
          action={<ViewAllLink href="/production" />}
        >
          <RecentScriptsList
            scripts={data.recentScripts}
            unavailable={panelUnavailable(data.recentScriptsAvailability)}
            restricted={panelRestricted(data.recentScriptsAvailability)}
          />
        </SectionPanel>
        <SectionPanel
          title="Pending Reviews"
          action={<ViewAllLink href="/reviews?status=pending" />}
        >
          <PendingReviewsList
            reviews={data.pendingReviews}
            restricted={panelRestricted(data.pendingReviewsAvailability)}
            unavailable={panelUnavailable(data.pendingReviewsAvailability)}
          />
        </SectionPanel>
      </div>

      <div className="mt-4">
        <SectionPanel
          title="Recent Activity"
          action={<ViewAllLink href="/production" />}
        >
          <ActivityTimeline
            items={data.recentActivity}
            restricted={panelRestricted(data.recentActivityAvailability)}
            unavailable={panelUnavailable(data.recentActivityAvailability)}
          />
        </SectionPanel>
      </div>
    </PageContainer>
  );
}
