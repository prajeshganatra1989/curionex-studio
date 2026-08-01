"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { BookOpen, Plus } from "lucide-react";

import { CreateKnowledgePackModal } from "@/components/projects/quick-create-modals";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/lib/api/client";
import { useProjectKnowledgePacks } from "@/lib/projects/hooks";
import { formatRelativeTime } from "@/lib/utils";

export function ProjectKnowledgePacksPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [createOpen, setCreateOpen] = useState(false);
  const { data, isLoading, isError, error, refetch } = useProjectKnowledgePacks(
    projectId,
    { page: 1, page_size: 50 },
  );

  return (
    <PageContainer>
      <PageHeader
        title="Knowledge Packs"
        description="Open a pack to research in the writing workspace."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Create Knowledge Pack
          </Button>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-20" />
          ))}
        </div>
      ) : null}

      {isError ? (
        <ErrorState
          message={
            error instanceof ApiError
              ? error.detail
              : "Unable to load Knowledge Packs."
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

      {!isLoading && !isError && (data?.items.length ?? 0) === 0 ? (
        <EmptyState
          title="No Knowledge Packs yet"
          description="Create a pack to start collecting research for this project."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              Create Knowledge Pack
            </Button>
          }
        />
      ) : null}

      {!isLoading && !isError && data && data.items.length > 0 ? (
        <ul className="divide-y divide-border rounded-xl border border-border bg-surface">
          {data.items.map((pack) => (
            <li key={pack.id}>
              <Link
                href={`/projects/${projectId}/knowledge-packs/${pack.id}`}
                className="flex items-center gap-3 px-4 py-4 transition hover:bg-surface-hover"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-brand-orange">
                  <BookOpen className="h-5 w-5" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="truncate font-medium text-foreground">
                      {pack.name}
                    </span>
                    <StatusBadge status={pack.status} />
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Updated {formatRelativeTime(pack.updated_at)}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}

      <CreateKnowledgePackModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        projectId={projectId}
      />
    </PageContainer>
  );
}
