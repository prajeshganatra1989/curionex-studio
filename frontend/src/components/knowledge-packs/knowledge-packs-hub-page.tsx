"use client";

import Link from "next/link";
import { BookOpen, FolderKanban } from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/lib/api/client";
import { useProjects } from "@/lib/projects/hooks";
import { formatRelativeTime } from "@/lib/utils";

/**
 * Global Knowledge Packs entry. Packs are project-scoped in the API, so this
 * hub routes creators into a project pack list / research workspace.
 */
export function KnowledgePacksHubPage() {
  const { data, isLoading, isError, error, refetch } = useProjects({
    page: 1,
    page_size: 12,
  });

  return (
    <PageContainer>
      <PageHeader
        title="Knowledge Packs"
        description="Open a project to write research in the Knowledge Pack workspace."
        actions={
          <Link
            href="/projects"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground transition hover:bg-surface-hover"
          >
            <FolderKanban className="h-4 w-4" />
            All projects
          </Link>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-20" />
          ))}
        </div>
      ) : null}

      {isError ? (
        <ErrorState
          message={
            error instanceof ApiError
              ? error.detail
              : "Unable to load projects."
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
          title="Create a project first"
          description="Knowledge Packs live inside projects. Start with one idea, then open the research workspace."
          action={
            <Link
              href="/projects"
              className="text-sm font-medium text-brand-orange hover:underline"
            >
              Go to Projects
            </Link>
          }
        />
      ) : null}

      {!isLoading && !isError && data && data.items.length > 0 ? (
        <ul className="divide-y divide-border rounded-xl border border-border bg-surface">
          {data.items.map((project) => (
            <li key={project.id}>
              <Link
                href={`/projects/${project.id}/packs`}
                className="flex items-center gap-3 px-4 py-4 transition hover:bg-surface-hover"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-brand-orange">
                  <BookOpen className="h-5 w-5" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[11px] text-brand-amber">
                      {project.project_code}
                    </span>
                    <StatusBadge status={project.status} />
                  </div>
                  <p className="mt-0.5 truncate text-sm font-medium text-foreground">
                    {project.name}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Open Knowledge Packs · Updated{" "}
                    {formatRelativeTime(project.updated_at)}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </PageContainer>
  );
}
