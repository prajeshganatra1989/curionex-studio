"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  Factory,
  FileText,
  FolderKanban,
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
import { greetingForHour } from "@/lib/utils";

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

function DemoMark() {
  return (
    <span className="rounded-md border border-border bg-surface px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
      Demo
    </span>
  );
}

function LiveMark() {
  return (
    <span className="rounded-md border border-brand-orange/30 bg-brand-orange/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-brand-amber">
      Live
    </span>
  );
}

export function DashboardPage() {
  const { user, api, status } = useAuth();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => getDashboardData(api),
    enabled: status === "authenticated",
  });

  const hour = new Date().getHours();
  const greeting = greetingForHour(hour);
  const firstName = user?.first_name ?? "there";

  if (isLoading || status === "loading") {
    return (
      <PageContainer>
        <DashboardSkeleton />
      </PageContainer>
    );
  }

  if (isError || !data) {
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
              onClick={() => void refetch()}
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
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {greeting}, {firstName}!{" "}
              <span aria-hidden className="inline-block">
                👋
              </span>
            </h1>
            {metrics.isDemo ? (
              <span className="rounded-md border border-border bg-surface px-2 py-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                Mixed live + demo
              </span>
            ) : null}
          </div>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground sm:text-base">
            Ready to create something amazing today?
          </p>
          <Link
            href="/production"
            data-testid="open-production-mode"
            className="mt-3 inline-flex w-fit items-center gap-2 rounded-lg border border-brand-orange/35 bg-brand-orange/10 px-3 py-2 text-sm font-medium text-brand-amber transition hover:bg-brand-orange/15"
          >
            <Factory className="h-4 w-4" aria-hidden />
            Open Production Mode
          </Link>
        </div>
        <div className="w-full max-w-sm shrink-0 lg:w-80">
          <DailyGoalCard goal={data.dailyGoal} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <MetricCard
          label="Projects"
          value={metrics.projects}
          hint="From project list total"
          icon={FolderKanban}
          accent="brand"
          isDemo={!metrics.projectsLive}
        />
        <MetricCard
          label="Knowledge Packs"
          value={metrics.knowledgePacks}
          hint="Total packs"
          icon={BookOpen}
          accent="brand"
          isDemo
        />
        <MetricCard
          label="Scripts"
          value={metrics.scripts}
          hint="Total scripts"
          icon={FileText}
          accent="brand"
          isDemo
        />
        <MetricCard
          label="Needs Revision"
          value={metrics.needingRevision}
          hint="From production quality"
          icon={AlertTriangle}
          accent="warning"
          isDemo={!metrics.productionLive}
        />
        <MetricCard
          label="Pending Reviews"
          value={metrics.pendingReviews}
          hint="Awaiting human review"
          icon={ClipboardList}
          accent="warning"
          isDemo={!metrics.pendingReviewsLive}
        />
        <MetricCard
          label="Approved Scripts"
          value={metrics.approvedScripts}
          hint={
            metrics.productionLive
              ? "Toward production goal"
              : "Completed"
          }
          icon={CheckCircle2}
          accent="success"
          isDemo={!metrics.productionLive}
        />
      </div>

      {metrics.productionLive ? (
        <p
          className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground"
          data-testid="ai-running-hint"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden />
          AI running:{" "}
          <span className="tabular-nums text-foreground">
            {metrics.aiRunning}
          </span>
          <span aria-hidden>·</span>
          Quality scores are advisory — never treated as Approved.
        </p>
      ) : null}

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <SectionPanel
          title="Recent Projects"
          action={
            <div className="flex items-center gap-2">
              {data.recentProjectsLive ? <LiveMark /> : <DemoMark />}
              <ViewAllLink href="/projects" />
            </div>
          }
        >
          <RecentProjectsList projects={data.recentProjects} />
        </SectionPanel>
        <SectionPanel
          title="Recent Scripts"
          action={
            <div className="flex items-center gap-2">
              <DemoMark />
              <ViewAllLink href="/scripts" />
            </div>
          }
        >
          <RecentScriptsList scripts={data.recentScripts} />
        </SectionPanel>
        <SectionPanel
          title="Pending Reviews"
          action={
            <div className="flex items-center gap-2">
              {data.pendingReviewsLive ? <LiveMark /> : <DemoMark />}
              <ViewAllLink href="/reviews?status=pending" />
            </div>
          }
        >
          <PendingReviewsList
            reviews={data.pendingReviews}
            restricted={data.pendingReviewsRestricted}
          />
        </SectionPanel>
      </div>

      <div className="mt-4">
        <SectionPanel
          title="Recent Activity"
          action={
            <div className="flex items-center gap-2">
              <DemoMark />
              <Link
                href="/activity"
                className="text-xs font-medium text-brand-orange hover:underline"
              >
                View all activity
              </Link>
            </div>
          }
        >
          <ActivityTimeline
            items={data.recentActivity}
            restricted={data.activityRestricted}
          />
        </SectionPanel>
      </div>
    </PageContainer>
  );
}
