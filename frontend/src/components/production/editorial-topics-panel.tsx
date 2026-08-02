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
      description="Available ideas ready for production."
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
          <dl className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-border/60 px-3 py-2">
              <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Available
              </dt>
              <dd
                className="mt-1 text-xl font-semibold tabular-nums"
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
                className="mt-1 text-xl font-semibold tabular-nums"
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
                className="mt-1 text-xl font-semibold tabular-nums"
                data-testid="topics-published"
              >
                {data.published}
              </dd>
            </div>
          </dl>
        ) : null}
      </div>
    </SectionPanel>
  );
}
