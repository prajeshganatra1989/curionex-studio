"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { ScriptQualityReviewView } from "@/components/scripts/script-quality-review-view";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { ApiError } from "@/lib/api/client";
import { useScript } from "@/lib/scripts/hooks";

export function ScriptQualityReviewPage() {
  const params = useParams<{
    projectId: string;
    scriptId: string;
    generationId: string;
  }>();
  const projectId = params.projectId;
  const scriptId = params.scriptId;
  const generationId = params.generationId;

  const scriptQuery = useScript(scriptId);

  if (scriptQuery.isLoading) {
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

  const script = scriptQuery.data;
  const workspaceHref = `/projects/${projectId}/scripts/${scriptId}`;

  return (
    <PageContainer>
      <PageHeader
        title="Script Quality Review"
        description={`${script.title} · Advisory AI review (never an approval)`}
        actions={
          <Link
            href={workspaceHref}
            className="inline-flex h-10 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Workspace
          </Link>
        }
      />

      <ScriptQualityReviewView
        scriptId={scriptId}
        generationId={generationId}
      />
    </PageContainer>
  );
}
