"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { useAiJobs, useCancelAiJob } from "@/lib/ai/hooks";
import { ApiError } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";

function JobsSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <LoadingSkeleton key={index} className="h-20" />
      ))}
    </div>
  );
}

function JobRow({ job }: { job: import("@/lib/ai/types").AiJob }) {
  const { toast } = useToast();
  const cancelJob = useCancelAiJob(job.id);
  const canCancel = job.status === "queued" || job.status === "running";

  async function handleCancel() {
    try {
      await cancelJob.mutateAsync();
      toast({ title: "Job cancelled", tone: "success" });
    } catch {
      toast({ title: "Unable to cancel job", tone: "error" });
    }
  }

  return (
    <li className="px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-mono text-sm text-foreground">{job.id}</p>
            <StatusBadge status={job.status} />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Model {job.model_id.slice(0, 8)}…
            <span aria-hidden> · </span>
            <time dateTime={job.created_at}>
              {formatRelativeTime(job.created_at)}
            </time>
            {job.duration_ms != null ? (
              <>
                <span aria-hidden> · </span>
                {job.duration_ms}ms
              </>
            ) : null}
          </p>
          {job.error_message ? (
            <p className="mt-2 text-xs text-danger">{job.error_message}</p>
          ) : null}
        </div>
        {canCancel ? (
          <Button
            type="button"
            variant="secondary"
            loading={cancelJob.isPending}
            onClick={() => void handleCancel()}
          >
            Cancel
          </Button>
        ) : null}
      </div>
    </li>
  );
}

export function JobsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1") || 1;
  const status = searchParams.get("status") || "";

  const params = useMemo(
    () => ({
      page,
      page_size: 12,
      status: status || undefined,
    }),
    [page, status],
  );

  const { data, isLoading, isError, error, refetch } = useAiJobs(params);

  function updateQuery(next: Record<string, string | null>) {
    const q = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(next)) {
      if (!value) q.delete(key);
      else q.set(key, value);
    }
    if (!("page" in next)) q.set("page", "1");
    router.replace(`/ai/jobs?${q.toString()}`);
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Job Monitor"
        description="Track queued and running generation jobs."
        actions={
          <Link
            href="/ai"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
          >
            Back to hub
          </Link>
        }
      />

      <div className="mb-4 sm:w-44">
        <TextSelect
          value={status}
          onChange={(event) =>
            updateQuery({ status: event.target.value || null })
          }
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </TextSelect>
      </div>

      {isLoading ? <JobsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You do not have permission to view AI jobs."
        />
      ) : null}

      {!isLoading && isError && !restricted ? (
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load jobs."
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
      ) : null}

      {!isLoading && !isError && items.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Jobs appear when generations are queued through the API."
        />
      ) : null}

      {!isLoading && !isError && items.length > 0 ? (
        <>
          <ul
            className="divide-y divide-border rounded-xl border border-border/70 bg-surface/40"
            data-testid="jobs-list"
          >
            {items.map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
          </ul>
          <div className="mt-4">
            <Pagination
              page={page}
              pageSize={params.page_size ?? 12}
              total={total}
              onPageChange={(nextPage) =>
                updateQuery({ page: String(nextPage) })
              }
            />
          </div>
        </>
      ) : null}
    </PageContainer>
  );
}
