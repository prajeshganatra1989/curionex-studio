"use client";

import Link from "next/link";
import { BookOpen, Sparkles } from "lucide-react";

import { ContentStandardPreview } from "@/components/editorial/content-standard-preview";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { SectionPanel } from "@/components/ui/section-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/lib/api/client";
import { useActiveContentStandard } from "@/lib/editorial/content-standard-hooks";
import { formatRelativeTime } from "@/lib/utils";

export function EditorialSettingsPage() {
  const activeQuery = useActiveContentStandard();
  const standard = activeQuery.data;
  const notFound =
    activeQuery.isError &&
    activeQuery.error instanceof ApiError &&
    activeQuery.error.status === 404;
  const restricted =
    activeQuery.isError &&
    activeQuery.error instanceof ApiError &&
    activeQuery.error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Editorial"
        description="Curionex Content Standard — the single editorial source of truth for AI prompts."
      />

      {activeQuery.isLoading ? (
        <div className="space-y-4" aria-busy="true">
          <LoadingSkeleton className="h-24" />
          <LoadingSkeleton className="h-64" />
        </div>
      ) : null}

      {restricted ? (
        <ErrorState
          title="Access restricted"
          message="You do not have permission to view the Content Standard."
        />
      ) : null}

      {activeQuery.isError && !notFound && !restricted ? (
        <ErrorState
          title="Unable to load Content Standard"
          message="Try again in a moment."
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void activeQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      ) : null}

      {notFound ? (
        <div data-testid="content-standard-empty">
          <EmptyState
            title="No active Content Standard"
            description="Seed Curionex Content Standard v1 to unlock consistent editorial guidance across AI prompts."
          />
        </div>
      ) : null}

      {standard ? (
        <div className="space-y-6" data-testid="editorial-settings">
          <SectionPanel title="Current Standard">
            <div className="grid gap-4 p-2 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Name
                </p>
                <p className="mt-1 text-sm font-medium text-foreground">
                  {standard.name}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Version
                </p>
                <p
                  className="mt-1 inline-flex items-center rounded-md bg-brand-orange/10 px-2 py-0.5 text-sm font-semibold text-brand-orange"
                  data-testid="content-standard-version-badge"
                >
                  v{standard.version}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Status
                </p>
                <div className="mt-1">
                  <StatusBadge status={standard.status} />
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Last Updated
                </p>
                <p className="mt-1 text-sm text-foreground">
                  {formatRelativeTime(standard.updated_at)}
                </p>
              </div>
            </div>
            <p className="mt-4 px-2 text-sm text-muted-foreground">
              Switch Version is coming soon. Activation is managed via the API
              today.
            </p>
          </SectionPanel>

          <SectionPanel title="Preview">
            <ContentStandardPreview standard={standard} />
          </SectionPanel>
        </div>
      ) : null}

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Link
          href="/settings"
          className="panel flex items-center gap-4 p-5 transition hover:border-brand-orange/40 hover:bg-surface-hover"
        >
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
            <BookOpen className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <h2 className="text-base font-semibold text-foreground">
              All settings
            </h2>
            <p className="text-sm text-muted-foreground">
              Return to the settings hub.
            </p>
          </div>
        </Link>
        <Link
          href="/ai/settings"
          className="panel flex items-center gap-4 p-5 transition hover:border-brand-orange/40 hover:bg-surface-hover"
        >
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
            <Sparkles className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <h2 className="text-base font-semibold text-foreground">
              AI Foundation
            </h2>
            <p className="text-sm text-muted-foreground">
              Providers, models, and generation defaults.
            </p>
          </div>
        </Link>
      </div>
    </PageContainer>
  );
}
