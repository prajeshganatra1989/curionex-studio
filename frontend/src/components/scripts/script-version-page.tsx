"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { PageContainer } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/lib/api/client";
import { useScript, useContentVersion } from "@/lib/scripts/hooks";
import { parseSnapshot } from "@/lib/scripts/snapshot";
import { formatRelativeTime } from "@/lib/utils";

type ScriptVersionPageProps = {
  projectId: string;
  scriptId: string;
  versionId: string;
};

export function ScriptVersionPage({
  projectId,
  scriptId,
  versionId,
}: ScriptVersionPageProps) {
  const scriptQuery = useScript(scriptId);
  const versionQuery = useContentVersion(versionId);

  if (scriptQuery.isLoading || versionQuery.isLoading) {
    return (
      <PageContainer>
        <LoadingSkeleton className="mb-4 h-10 w-48" />
        <LoadingSkeleton className="h-96" />
      </PageContainer>
    );
  }

  if (scriptQuery.isError || !scriptQuery.data) {
    const status =
      scriptQuery.error instanceof ApiError ? scriptQuery.error.status : 0;
    return (
      <PageContainer>
        <EmptyState
          title={status === 404 ? "Script not found" : "Unable to load script"}
          description="Return to the workspace and try again."
          action={
            <Link
              href={`/projects/${projectId}/scripts`}
              className="text-sm text-brand-orange underline"
            >
              Back to Scripts
            </Link>
          }
        />
      </PageContainer>
    );
  }

  if (versionQuery.isError || !versionQuery.data) {
    const status =
      versionQuery.error instanceof ApiError ? versionQuery.error.status : 0;
    return (
      <PageContainer>
        <EmptyState
          title={status === 404 ? "Version not found" : "Unable to load version"}
          action={
            <Link
              href={`/projects/${projectId}/scripts/${scriptId}`}
              className="text-sm text-brand-orange underline"
            >
              Back to Workspace
            </Link>
          }
        />
      </PageContainer>
    );
  }

  const script = scriptQuery.data;
  const version = versionQuery.data;

  if (
    script.project_id !== projectId ||
    (version.script_id && version.script_id !== scriptId)
  ) {
    return (
      <PageContainer>
        <EmptyState
          title="Version not in this script"
          description="Open the version from its script workspace."
          action={
            <Link
              href={`/projects/${script.project_id}/scripts/${scriptId}`}
              className="text-sm text-brand-orange underline"
            >
              Go to workspace
            </Link>
          }
        />
      </PageContainer>
    );
  }

  const snapshot = parseSnapshot(version.content);
  const workspaceHref = `/projects/${projectId}/scripts/${scriptId}`;

  return (
    <PageContainer>
      <Link
        href={workspaceHref}
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Workspace
      </Link>

      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Version {version.version_number}
          </h1>
          <StatusBadge status={version.status} />
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {script.script_code}
          <span aria-hidden> · </span>
          {script.title}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Snapshot created{" "}
          <time dateTime={version.created_at}>
            {formatRelativeTime(version.created_at)}
          </time>
        </p>
      </div>

      <div className="space-y-6" data-testid="script-version-snapshot">
        {snapshot.sections.map((section) => (
          <section
            key={section.key}
            className="rounded-xl border border-border/70 bg-surface/40 p-4"
            data-testid={`version-section-${section.key}`}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              {section.title}
            </h2>
            <pre className="mt-3 whitespace-pre-wrap text-sm text-foreground">
              {section.content.trim() || "—"}
            </pre>
          </section>
        ))}
      </div>
    </PageContainer>
  );
}
