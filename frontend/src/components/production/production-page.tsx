"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { LayoutGrid, Library, List, Plus, Settings2 } from "lucide-react";

import { AiOpsPanel } from "@/components/production/ai-ops-panel";
import { EditorialTopicsPanel } from "@/components/production/editorial-topics-panel";
import { GoalHero } from "@/components/production/goal-hero";
import { ProductionSettingsDialog } from "@/components/production/production-settings-dialog";
import { QualityPanel } from "@/components/production/quality-panel";
import {
  QuickFilters,
  type ProductionFilterState,
} from "@/components/production/quick-filters";
import { QueueView } from "@/components/production/queue-view";
import { RecentActivity } from "@/components/production/recent-activity";
import { StageBoard } from "@/components/production/stage-board";
import { TodayPanel } from "@/components/production/today-panel";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { ApiError } from "@/lib/api/client";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import {
  useProductionActivity,
  useProductionMetrics,
  useProductionOverview,
  useProductionQueue,
} from "@/lib/production/hooks";
import type { ProductionViewMode } from "@/lib/production/types";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

function readBool(value: string | null): boolean {
  return value === "1" || value === "true";
}

function filtersFromSearchParams(
  searchParams: URLSearchParams,
): ProductionFilterState {
  return {
    search: searchParams.get("search") || "",
    production_stage: searchParams.get("production_stage") || "",
    project_id: searchParams.get("project_id") || "",
    category_id: searchParams.get("category_id") || "",
    tag_id: searchParams.get("tag_id") || "",
    quality_band: searchParams.get("quality_band") || "",
    ai_job_status: searchParams.get("ai_job_status") || "",
    stale_quality: readBool(searchParams.get("stale_quality")),
    blocked_only: readBool(searchParams.get("blocked_only")),
    pending_approval: readBool(searchParams.get("pending_approval")),
    sort: searchParams.get("sort") || "priority",
  };
}

function hasActiveFilters(filters: ProductionFilterState): boolean {
  return (
    Boolean(filters.search.trim()) ||
    Boolean(filters.production_stage) ||
    Boolean(filters.project_id) ||
    Boolean(filters.category_id) ||
    Boolean(filters.tag_id) ||
    Boolean(filters.quality_band) ||
    Boolean(filters.ai_job_status) ||
    filters.stale_quality ||
    filters.blocked_only ||
    filters.pending_approval ||
    (Boolean(filters.sort) && filters.sort !== "priority")
  );
}

export function ProductionPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1") || 1;
  const view: ProductionViewMode =
    searchParams.get("view") === "board" ? "board" : "queue";

  const filters = useMemo(
    () => filtersFromSearchParams(searchParams),
    [searchParams],
  );

  const [searchInput, setSearchInput] = useState(filters.search);
  const debouncedSearch = useDebouncedValue(searchInput, 350);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  useEffect(() => {
    const next = debouncedSearch.trim();
    if (next === filters.search) return;
    const q = new URLSearchParams(searchParams.toString());
    if (next) q.set("search", next);
    else q.delete("search");
    q.set("page", "1");
    router.replace(`/production?${q.toString()}`);
  }, [debouncedSearch, filters.search, router, searchParams]);

  function updateQuery(next: Record<string, string | null>) {
    const q = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(next)) {
      if (!value) q.delete(key);
      else q.set(key, value);
    }
    if (!("page" in next)) q.set("page", "1");
    router.replace(`/production?${q.toString()}`);
  }

  function onFilterChange(partial: Partial<ProductionFilterState>) {
    const merged = { ...filters, ...partial };
    updateQuery({
      search: merged.search.trim() || null,
      production_stage: merged.production_stage || null,
      project_id: merged.project_id || null,
      category_id: merged.category_id || null,
      tag_id: merged.tag_id || null,
      quality_band: merged.quality_band || null,
      ai_job_status: merged.ai_job_status || null,
      stale_quality: merged.stale_quality ? "1" : null,
      blocked_only: merged.blocked_only ? "1" : null,
      pending_approval: merged.pending_approval ? "1" : null,
      sort: merged.sort && merged.sort !== "priority" ? merged.sort : null,
      view: view === "board" ? "board" : null,
    });
  }

  function resetFilters() {
    setSearchInput("");
    const q = new URLSearchParams();
    if (view === "board") q.set("view", "board");
    const qs = q.toString();
    router.replace(qs ? `/production?${qs}` : "/production");
  }

  const queueParams = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      production_stage: filters.production_stage || undefined,
      project_id: filters.project_id || undefined,
      category_id: filters.category_id || undefined,
      tag_id: filters.tag_id || undefined,
      search: filters.search.trim() || undefined,
      quality_band: filters.quality_band || undefined,
      ai_job_status: filters.ai_job_status || undefined,
      stale_quality: filters.stale_quality || undefined,
      blocked_only: filters.blocked_only || undefined,
      pending_approval: filters.pending_approval || undefined,
      sort: filters.sort || "priority",
    }),
    [page, filters],
  );

  const overviewQuery = useProductionOverview({ poll: true });
  const queueQuery = useProductionQueue(queueParams);
  const metricsQuery = useProductionMetrics("7d");
  const activityQuery = useProductionActivity(12);

  const overview = overviewQuery.data;
  const stageTotal = useMemo(() => {
    if (!overview) return 0;
    return Object.values(overview.stage_counts).reduce((sum, n) => sum + n, 0);
  }, [overview]);

  const filtersActive = hasActiveFilters(filters);
  const isEmptyCatalog =
    !filtersActive &&
    overview &&
    stageTotal === 0 &&
    !queueQuery.isLoading &&
    (queueQuery.data?.total ?? 0) === 0;

  const restricted =
    overviewQuery.isError &&
    overviewQuery.error instanceof ApiError &&
    overviewQuery.error.status === 403;

  if (overviewQuery.isLoading && !overview) {
    return (
      <PageContainer>
        <PageHeader
          title="Production Mode"
          description="Track the path to 120 approved scripts."
        />
        <div className="space-y-4" aria-busy="true">
          <LoadingSkeleton className="h-48" />
          <LoadingSkeleton className="h-24" />
          <LoadingSkeleton className="h-64" />
        </div>
      </PageContainer>
    );
  }

  if (restricted) {
    return (
      <PageContainer>
        <PageHeader title="Production Mode" />
        <EmptyState
          title="Access restricted"
          description="You do not have permission to view Production Mode."
        />
      </PageContainer>
    );
  }

  if (overviewQuery.isError && !overview) {
    return (
      <PageContainer>
        <PageHeader title="Production Mode" />
        <ErrorState
          message={
            overviewQuery.error instanceof ApiError
              ? overviewQuery.error.detail
              : "Unable to load production overview."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void overviewQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="Production Mode"
        description="Queue, stage board, and AI ops for the approved-script journey."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              className="h-10"
              onClick={() => setSettingsOpen(true)}
              data-testid="open-settings"
            >
              <Settings2 className="h-4 w-4" />
              Settings
            </Button>
            <Link
              href="/topics"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
            >
              <Library className="h-4 w-4" />
              Browse Topics
            </Link>
            <Link
              href="/projects"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-gradient px-4 text-sm font-semibold text-black shadow-[var(--glow-brand)] hover:brightness-110"
            >
              <Plus className="h-4 w-4" />
              New project
            </Link>
          </div>
        }
      />

      {overview ? <GoalHero goals={overview.goals} className="mb-4" /> : null}

      <div className="mb-4 grid gap-4 lg:grid-cols-3">
        <AiOpsPanel
          ai={overview?.ai}
          isLoading={overviewQuery.isLoading}
        />
        <QualityPanel
          quality={overview?.quality}
          isLoading={overviewQuery.isLoading}
        />
        <TodayPanel
          goals={overview?.goals}
          metrics={metricsQuery.data}
          isLoading={metricsQuery.isLoading}
        />
      </div>

      <div className="mb-4">
        <EditorialTopicsPanel />
      </div>

      {isEmptyCatalog ? (
        <div data-testid="production-empty" className="mb-4">
          <EmptyState
            title="No projects in production yet"
            description="Create a project and start a Knowledge Pack to begin the path to 120 approved scripts."
            action={
              <Link
                href="/projects"
                className="mt-2 inline-flex h-10 items-center justify-center rounded-lg bg-brand-gradient px-4 text-sm font-semibold text-black"
              >
                Create project
              </Link>
            }
          />
        </div>
      ) : (
        <>
          <div className="mb-4 space-y-3">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0 flex-1">
                <QuickFilters
                  filters={filters}
                  searchInput={searchInput}
                  onSearchInputChange={setSearchInput}
                  onChange={onFilterChange}
                  onReset={resetFilters}
                />
              </div>
              <div
                className="flex shrink-0 self-start rounded-lg border border-border p-0.5"
                role="tablist"
                aria-label="View mode"
              >
                <ViewTab
                  active={view === "queue"}
                  onClick={() => updateQuery({ view: null })}
                  icon={List}
                  label="Queue"
                />
                <ViewTab
                  active={view === "board"}
                  onClick={() => updateQuery({ view: "board" })}
                  icon={LayoutGrid}
                  label="Stage board"
                />
              </div>
            </div>
          </div>

          {/* Queue is primary on mobile; board is available as stacked groups */}
          {view === "queue" ? (
            <QueueView
              items={queueQuery.data?.items ?? []}
              page={page}
              pageSize={PAGE_SIZE}
              total={queueQuery.data?.total ?? 0}
              isLoading={queueQuery.isLoading}
              isError={queueQuery.isError}
              errorMessage={
                queueQuery.error instanceof ApiError
                  ? queueQuery.error.detail
                  : undefined
              }
              onPageChange={(nextPage) =>
                updateQuery({ page: String(nextPage) })
              }
              onRetry={() => void queueQuery.refetch()}
              emptyTitle={filtersActive ? "No matches" : "Queue is empty"}
              emptyDescription={
                filtersActive
                  ? "Try clearing filters to see more items."
                  : "Scripts and projects needing attention will appear here."
              }
              emptyAction={
                filtersActive ? (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={resetFilters}
                  >
                    Clear filters
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div data-testid="board-view">
              {queueQuery.isLoading ? (
                <LoadingSkeleton className="h-64" />
              ) : queueQuery.isError ? (
                <ErrorState
                  message={
                    queueQuery.error instanceof ApiError
                      ? queueQuery.error.detail
                      : "Unable to load board."
                  }
                  action={
                    <button
                      type="button"
                      className="text-sm text-brand-orange underline"
                      onClick={() => void queueQuery.refetch()}
                    >
                      Try again
                    </button>
                  }
                />
              ) : (
                <StageBoard
                  items={queueQuery.data?.items ?? []}
                  stageCounts={overview?.stage_counts}
                  className="md:flex-row"
                />
              )}
            </div>
          )}
        </>
      )}

      <div className="mt-4">
        <RecentActivity
          items={activityQuery.data?.items ?? []}
          restricted={activityQuery.data?.restricted}
          isLoading={activityQuery.isLoading}
        />
      </div>

      <ProductionSettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </PageContainer>
  );
}

function ViewTab({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof List;
  label: string;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cn(
        "inline-flex h-9 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition",
        active
          ? "bg-surface-elevated text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {label}
    </button>
  );
}
