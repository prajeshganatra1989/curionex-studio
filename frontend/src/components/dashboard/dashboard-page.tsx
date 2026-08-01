"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  CheckCircle2,
  ClipboardList,
  FileText,
  FolderKanban,
  PenLine,
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

export function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardData,
  });

  const hour = new Date().getHours();
  const greeting = greetingForHour(hour);
  const firstName = user?.first_name ?? "there";

  if (isLoading) {
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
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            {greeting}, {firstName}!
          </h1>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">
            Ready to create something amazing today?
          </p>
        </div>
        {metrics.isDemo ? (
          <span className="self-start rounded-md border border-border bg-surface px-2 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
            Demo dashboard data
          </span>
        ) : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <DailyGoalCard goal={data.dailyGoal} />
        <div className="panel flex flex-col justify-center gap-2 p-5">
          <p className="text-sm text-muted-foreground">Creator focus</p>
          <p className="text-lg font-semibold text-foreground">
            Prepare premium scripts. Ship two Shorts a day.
          </p>
          <p className="text-sm text-muted-foreground">
            Keep projects moving from Knowledge Pack → Script → Version →
            Review.
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Projects"
          value={metrics.projects}
          icon={FolderKanban}
          accent="brand"
        />
        <MetricCard
          label="Knowledge Packs"
          value={metrics.knowledgePacks}
          icon={BookOpen}
          accent="info"
        />
        <MetricCard
          label="Scripts"
          value={metrics.scripts}
          icon={FileText}
          accent="brand"
        />
        <MetricCard
          label="Draft Scripts"
          value={metrics.draftScripts}
          icon={PenLine}
          accent="warning"
        />
        <MetricCard
          label="Pending Reviews"
          value={metrics.pendingReviews}
          icon={ClipboardList}
          accent="warning"
        />
        <MetricCard
          label="Approved Scripts"
          value={metrics.approvedScripts}
          icon={CheckCircle2}
          accent="success"
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <SectionPanel
          title="Recent Projects"
          description="Jump back into active production"
        >
          <RecentProjectsList projects={data.recentProjects} />
        </SectionPanel>
        <SectionPanel
          title="Recent Scripts"
          description="Workspace documents in motion"
        >
          <RecentScriptsList scripts={data.recentScripts} />
        </SectionPanel>
        <SectionPanel
          title="Pending Reviews"
          description="Approvals waiting on a decision"
        >
          <PendingReviewsList reviews={data.pendingReviews} />
        </SectionPanel>
        <SectionPanel
          title="Recent Activity"
          description="What changed across the studio"
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
