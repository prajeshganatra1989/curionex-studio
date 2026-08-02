"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { useAiGeneration, useAiGenerations } from "@/lib/ai/hooks";
import type { AiGeneration } from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";

function GenerationsSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <LoadingSkeleton key={index} className="h-16" />
      ))}
    </div>
  );
}

function formatCost(value: number | null): string {
  if (value == null) return "—";
  return `$${value.toFixed(4)}`;
}

function GenerationDetail({ generation }: { generation: AiGeneration }) {
  return (
    <div className="space-y-4" data-testid="generation-detail">
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">Job</dt>
          <dd className="font-mono text-xs text-foreground">
            {generation.job_id}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Created</dt>
          <dd className="text-foreground">
            {formatRelativeTime(generation.created_at)}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Tokens in</dt>
          <dd className="tabular-nums text-foreground">
            {generation.tokens_input ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Tokens out</dt>
          <dd className="tabular-nums text-foreground">
            {generation.tokens_output ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Cost</dt>
          <dd className="tabular-nums text-foreground">
            {formatCost(generation.cost_usd)}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Latency</dt>
          <dd className="tabular-nums text-foreground">
            {generation.latency_ms != null
              ? `${generation.latency_ms}ms`
              : "—"}
          </dd>
        </div>
      </dl>

      <div>
        <h3 className="mb-2 text-sm font-medium text-foreground">Output</h3>
        <pre className="max-h-64 overflow-auto rounded-lg border border-border bg-background p-3 text-xs text-foreground whitespace-pre-wrap">
          {generation.output_text?.trim()
            ? generation.output_text
            : "(No output yet)"}
        </pre>
      </div>

      {Object.keys(generation.input_variables).length > 0 ? (
        <div>
          <h3 className="mb-2 text-sm font-medium text-foreground">
            Input variables
          </h3>
          <pre className="rounded-lg border border-border bg-background p-3 text-xs text-foreground">
            {JSON.stringify(generation.input_variables, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}

export function GenerationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const page = Number(searchParams.get("page") || "1") || 1;

  const params = useMemo(
    () => ({
      page,
      page_size: 12,
    }),
    [page],
  );

  const { data, isLoading, isError, error, refetch } = useAiGenerations(params);
  const detailQuery = useAiGeneration(selectedId);

  function updatePage(nextPage: number) {
    const q = new URLSearchParams(searchParams.toString());
    q.set("page", String(nextPage));
    router.replace(`/ai/generations?${q.toString()}`);
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Generation History"
        description="Read-only log of completed generations."
        actions={
          <Link
            href="/ai"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
          >
            Back to hub
          </Link>
        }
      />

      {isLoading ? <GenerationsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You do not have permission to view generations."
        />
      ) : null}

      {!isLoading && isError && !restricted ? (
        <ErrorState
          message={
            error instanceof ApiError
              ? error.detail
              : "Unable to load generations."
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
          title="No generations yet"
          description="Completed jobs will appear here once the backend records outputs."
        />
      ) : null}

      {!isLoading && !isError && items.length > 0 ? (
        <>
          <ul
            className="divide-y divide-border rounded-xl border border-border/70 bg-surface/40"
            data-testid="generations-list"
          >
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="flex w-full items-start justify-between gap-3 px-4 py-4 text-left transition hover:bg-surface-hover"
                  onClick={() => setSelectedId(item.id)}
                >
                  <div className="min-w-0">
                    <p className="font-mono text-sm text-foreground">
                      {item.id.slice(0, 12)}…
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      <time dateTime={item.created_at}>
                        {formatRelativeTime(item.created_at)}
                      </time>
                      {item.tokens_input != null ? (
                        <>
                          <span aria-hidden> · </span>
                          {item.tokens_input}+{item.tokens_output ?? 0} tokens
                        </>
                      ) : null}
                      {item.cost_usd != null ? (
                        <>
                          <span aria-hidden> · </span>
                          {formatCost(item.cost_usd)}
                        </>
                      ) : null}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs text-brand-orange">
                    View
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <Pagination
              page={page}
              pageSize={params.page_size ?? 12}
              total={total}
              onPageChange={updatePage}
            />
          </div>
        </>
      ) : null}

      <Modal
        open={Boolean(selectedId)}
        onClose={() => setSelectedId(null)}
        title="Generation detail"
        size="lg"
      >
        {detailQuery.isLoading ? (
          <LoadingSkeleton className="h-40" />
        ) : null}
        {detailQuery.data ? (
          <GenerationDetail generation={detailQuery.data} />
        ) : null}
        {detailQuery.isError ? (
          <ErrorState message="Unable to load generation detail." />
        ) : null}
      </Modal>
    </PageContainer>
  );
}
