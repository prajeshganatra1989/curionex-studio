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
import { StatusBadge } from "@/components/ui/status-badge";
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

function isApplied(generation: AiGeneration): boolean {
  return Boolean(generation.applied_sections && generation.applied_sections.length > 0);
}

function draftLink(generation: AiGeneration): string | null {
  if (!generation.knowledge_pack_id || !generation.project_id) return null;
  return `/projects/${generation.project_id}/knowledge-packs/${generation.knowledge_pack_id}`;
}

function GenerationDetail({ generation }: { generation: AiGeneration }) {
  const link = draftLink(generation);
  return (
    <div className="space-y-4" data-testid="generation-detail">
      {generation.purpose === "knowledge_pack.draft" ? (
        <div
          className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-xs text-foreground"
          role="note"
        >
          AI-generated content requires review and source verification before
          publishing.
        </div>
      ) : null}

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
          <dt className="text-muted-foreground">Purpose</dt>
          <dd className="text-foreground">{generation.purpose ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Applied</dt>
          <dd className="text-foreground">
            {isApplied(generation)
              ? `Yes — ${generation.applied_sections?.join(", ")}`
              : "Not applied"}
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
          <dt className="text-muted-foreground">Tokens total</dt>
          <dd className="tabular-nums text-foreground">
            {generation.tokens_total ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Estimated cost</dt>
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

      {link ? (
        <Link
          href={link}
          className="inline-flex text-sm font-medium text-brand-orange underline"
        >
          Open Draft in Knowledge Pack
        </Link>
      ) : null}

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
            {items.map((item) => {
              const link = draftLink(item);
              return (
                <li key={item.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3 px-4 py-4">
                    <button
                      type="button"
                      className="min-w-0 flex-1 text-left"
                      onClick={() => setSelectedId(item.id)}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-mono text-sm text-foreground">
                          {item.id.slice(0, 12)}…
                        </p>
                        {item.purpose ? (
                          <span className="rounded-md border border-border bg-surface-hover px-1.5 py-0.5 text-[11px] text-muted-foreground">
                            {item.purpose}
                          </span>
                        ) : null}
                        {isApplied(item) ? (
                          <StatusBadge status="completed" />
                        ) : null}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        <time dateTime={item.created_at}>
                          {formatRelativeTime(item.created_at)}
                        </time>
                        {item.tokens_total != null || item.tokens_input != null ? (
                          <>
                            <span aria-hidden> · </span>
                            {item.tokens_total ??
                              (item.tokens_input ?? 0) + (item.tokens_output ?? 0)}{" "}
                            tokens
                          </>
                        ) : null}
                        {item.cost_usd != null ? (
                          <>
                            <span aria-hidden> · </span>
                            {formatCost(item.cost_usd)} est.
                          </>
                        ) : null}
                      </p>
                    </button>
                    <div className="flex shrink-0 items-center gap-3">
                      {link ? (
                        <Link
                          href={link}
                          className="text-xs font-medium text-brand-orange underline"
                        >
                          Open Draft
                        </Link>
                      ) : null}
                      <button
                        type="button"
                        className="text-xs text-brand-orange"
                        onClick={() => setSelectedId(item.id)}
                      >
                        View
                      </button>
                    </div>
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
