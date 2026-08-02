"use client";

import Link from "next/link";
import { Library } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { SectionPanel } from "@/components/ui/section-panel";
import { ApiError } from "@/lib/api/client";
import { useEditorialTopicSummary } from "@/lib/editorial/hooks";

export function EditorialTopicsPanel({ className }: { className?: string }) {
  const { data, isLoading, isError, error } = useEditorialTopicSummary();

  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <SectionPanel
      title="Editorial Library"
      description="Production catalog waves and topic pipeline."
      className={className}
      action={
        <Link
          href="/topics"
          className="inline-flex items-center gap-1 text-xs font-medium text-brand-orange hover:underline"
          data-testid="browse-topics"
        >
          <Library className="h-3.5 w-3.5" aria-hidden />
          Browse Topics
        </Link>
      }
    >
      <div data-testid="editorial-topics-panel">
        {isLoading ? (
          <div className="space-y-2" aria-busy="true">
            <LoadingSkeleton className="h-10" />
            <LoadingSkeleton className="h-10" />
            <LoadingSkeleton className="h-10" />
          </div>
        ) : null}

        {restricted ? (
          <EmptyState
            title="Topics restricted"
            description="You need editorial_topics.view to see library counts."
          />
        ) : null}

        {isError && !restricted ? (
          <EmptyState
            title="Temporarily unavailable"
            description="Could not load editorial topic counts."
          />
        ) : null}

        {!isLoading && !isError && data ? (
          <div className="space-y-3">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Wave 1 remaining
                </dt>
                <dd
                  className="mt-1 text-xl font-semibold tabular-nums"
                  data-testid="topics-wave-1-remaining"
                >
                  {data.wave_1_remaining}
                </dd>
              </div>
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Wave 2 remaining
                </dt>
                <dd
                  className="mt-1 text-xl font-semibold tabular-nums"
                  data-testid="topics-wave-2-remaining"
                >
                  {data.wave_2_remaining}
                </dd>
              </div>
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Approved in wave {data.current_wave}
                </dt>
                <dd
                  className="mt-1 text-xl font-semibold tabular-nums"
                  data-testid="topics-approved-current-wave"
                >
                  {data.approved_in_current_wave}
                </dd>
              </div>
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Remaining in wave
                </dt>
                <dd
                  className="mt-1 text-xl font-semibold tabular-nums"
                  data-testid="topics-remaining-in-wave"
                >
                  {data.remaining_in_wave}
                </dd>
              </div>
            </dl>
            <dl className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Available
                </dt>
                <dd
                  className="mt-1 text-lg font-semibold tabular-nums"
                  data-testid="topics-available"
                >
                  {data.available}
                </dd>
              </div>
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  In progress
                </dt>
                <dd
                  className="mt-1 text-lg font-semibold tabular-nums"
                  data-testid="topics-in-progress"
                >
                  {data.in_progress}
                </dd>
              </div>
              <div className="rounded-lg border border-border/60 px-3 py-2">
                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Published
                </dt>
                <dd
                  className="mt-1 text-lg font-semibold tabular-nums"
                  data-testid="topics-published"
                >
                  {data.published}
                </dd>
              </div>
            </dl>
          </div>
        ) : null}
      </div>
    </SectionPanel>
  );
}
