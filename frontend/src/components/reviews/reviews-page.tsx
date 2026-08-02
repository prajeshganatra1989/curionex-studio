"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { AvatarInitials } from "@/components/ui/avatar-initials";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge } from "@/components/ui/status-badge";
import { TextInput, TextSelect } from "@/components/ui/field";
import { ApiError } from "@/lib/api/client";
import { useReviews } from "@/lib/reviews/hooks";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { formatRelativeTime } from "@/lib/utils";

function ReviewsSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <LoadingSkeleton key={index} className="h-20" />
      ))}
    </div>
  );
}

export function ReviewsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1") || 1;
  const status = searchParams.get("status") || "";
  const projectId = searchParams.get("project_id") || "";
  const search = searchParams.get("search") || "";

  const [searchInput, setSearchInput] = useState(search);
  const debouncedSearch = useDebouncedValue(searchInput, 350);

  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  useEffect(() => {
    const next = debouncedSearch.trim();
    if (next === search) return;
    const q = new URLSearchParams(searchParams.toString());
    if (next) q.set("search", next);
    else q.delete("search");
    q.set("page", "1");
    router.replace(`/reviews?${q.toString()}`);
  }, [debouncedSearch, search, router, searchParams]);

  const params = useMemo(
    () => ({
      page,
      page_size: 12,
      status: status || undefined,
      project_id: projectId || undefined,
      search: search.trim() || undefined,
    }),
    [page, status, projectId, search],
  );

  const { data, isLoading, isError, error, refetch } = useReviews(params);

  function updateQuery(next: Record<string, string | null>) {
    const q = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(next)) {
      if (!value) q.delete(key);
      else q.set(key, value);
    }
    if (!("page" in next)) q.set("page", "1");
    router.replace(`/reviews?${q.toString()}`);
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Reviews"
        description="Approval inbox for script content versions awaiting review."
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <TextInput
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by script or project…"
            className="pl-9"
            aria-label="Search reviews"
          />
        </div>
        <TextSelect
          value={status}
          onChange={(event) =>
            updateQuery({ status: event.target.value || null })
          }
          aria-label="Filter by status"
          className="sm:w-44"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="cancelled">Cancelled</option>
        </TextSelect>
      </div>

      {isLoading ? <ReviewsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You do not have permission to view the approval inbox."
        />
      ) : null}

      {!isLoading && isError && !restricted ? (
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load reviews."
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
          title="No reviews found"
          description="Submitted approvals will appear here when scripts enter review."
        />
      ) : null}

      {!isLoading && !isError && items.length > 0 ? (
        <>
          <ul
            className="divide-y divide-border rounded-xl border border-border/70 bg-surface/40"
            data-testid="reviews-list"
          >
            {items.map((item) => {
              const submitter = `${item.requested_by.first_name} ${item.requested_by.last_name}`;
              const title = item.script?.title ?? item.content_version.title;
              const workspaceHref =
                item.script && item.project
                  ? `/projects/${item.project.id}/scripts/${item.script.id}`
                  : null;
              return (
                <li key={item.id}>
                  <div className="flex items-start gap-3 px-4 py-4 transition hover:bg-surface-hover">
                    <Link
                      href={`/reviews/${item.id}`}
                      className="flex min-w-0 flex-1 items-start gap-3"
                    >
                      <AvatarInitials name={submitter} />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="truncate text-sm font-medium text-foreground">
                            {title}
                          </p>
                          <StatusBadge status={item.status} />
                        </div>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {item.project.project_code}
                          {item.script ? (
                            <>
                              <span aria-hidden> · </span>
                              {item.script.script_code}
                            </>
                          ) : null}
                          <span aria-hidden> · </span>
                          v{item.content_version.version_number}
                          <span aria-hidden> · </span>
                          <time dateTime={item.created_at}>
                            {formatRelativeTime(item.created_at)}
                          </time>
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Requested by {submitter}
                        </p>
                      </div>
                    </Link>
                    {workspaceHref ? (
                      <Link
                        href={workspaceHref}
                        className="shrink-0 text-xs text-brand-orange hover:underline"
                      >
                        Workspace
                      </Link>
                    ) : null}
                  </div>
                </li>
              );
            })}
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
