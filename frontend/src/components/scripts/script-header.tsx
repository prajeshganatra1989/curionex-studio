"use client";

import Link from "next/link";
import { ArrowLeft, List, Save } from "lucide-react";

import { SaveIndicator } from "@/components/knowledge-packs/save-indicator";
import {
  WorkflowActionButton,
  type WorkflowActionKind,
} from "@/components/scripts/workflow-action-button";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Project, ScriptDetail } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/utils";

type ScriptHeaderProps = {
  project: Project | undefined;
  script: ScriptDetail;
  knowledgePackName: string | null;
  saving: boolean;
  dirty: boolean;
  savedLabel: string | null;
  saveFailed?: boolean;
  workflowAction: { kind: WorkflowActionKind; label: string };
  workflowLoading?: boolean;
  productionPackageEligible?: boolean;
  onSave: () => void;
  onReviewQuality?: () => void;
  onCreateVersion: () => void;
  onWorkflowAction: (kind: WorkflowActionKind) => void;
  onOpenNav: () => void;
  onEditMeta: () => void;
  onGenerateProductionPackage?: () => void;
};

export function ScriptHeader({
  project,
  script,
  knowledgePackName,
  saving,
  dirty,
  savedLabel,
  saveFailed,
  workflowAction,
  workflowLoading,
  productionPackageEligible,
  onSave,
  onReviewQuality,
  onCreateVersion,
  onWorkflowAction,
  onOpenNav,
  onEditMeta,
  onGenerateProductionPackage,
}: ScriptHeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border/80 bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[96rem] flex-col gap-4 px-4 py-4 sm:px-8 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground lg:hidden"
              aria-label="Open document navigator"
              onClick={onOpenNav}
            >
              <List className="h-4 w-4" />
            </button>
            <Link
              href={`/projects/${script.project_id}`}
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Project
            </Link>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {project ? (
              <span className="font-mono text-xs text-brand-amber">
                {project.project_code}
              </span>
            ) : null}
            <span className="font-mono text-xs text-muted-foreground">
              {script.script_code}
            </span>
            <StatusBadge status={script.status} />
          </div>

          <div className="mt-1.5 flex flex-wrap items-baseline gap-2">
            <h1 className="truncate text-2xl font-semibold tracking-tight text-foreground">
              {script.title}
            </h1>
            <button
              type="button"
              className="text-xs text-brand-orange underline-offset-2 hover:underline"
              onClick={onEditMeta}
            >
              Edit details
            </button>
          </div>

          <p className="mt-1 truncate text-sm text-muted-foreground">
            {project?.name ?? "Project"}
            {knowledgePackName ? ` · ${knowledgePackName}` : " · No Knowledge Pack"}
            {` · Updated ${formatRelativeTime(script.updated_at)}`}
          </p>
        </div>

        <div className="flex flex-col items-stretch gap-2 sm:items-end">
          <div className="flex flex-wrap items-center gap-2 sm:justify-end">
            <SaveIndicator
              saving={saving}
              dirty={dirty || Boolean(saveFailed)}
              savedLabel={saveFailed ? "Save failed" : savedLabel}
            />
            <Button
              type="button"
              onClick={onSave}
              loading={saving}
              disabled={!dirty || saving}
              aria-label="Save changes"
            >
              <Save className="h-4 w-4" />
              Save Changes
            </Button>
            {onReviewQuality ? (
              <Button
                type="button"
                variant="secondary"
                onClick={onReviewQuality}
                disabled={saving}
                aria-label="Review script quality"
                data-testid="script-header-review-quality"
              >
                Review Script Quality
              </Button>
            ) : null}
            {productionPackageEligible && onGenerateProductionPackage ? (
              <Button
                type="button"
                variant="secondary"
                onClick={onGenerateProductionPackage}
                disabled={saving}
                aria-label="Generate production package"
                data-testid="script-header-production-package"
              >
                Generate Production Package
              </Button>
            ) : null}
            <Button
              type="button"
              variant="secondary"
              onClick={onCreateVersion}
              disabled={saving}
              aria-label="Create version"
            >
              Create Version
            </Button>
            <WorkflowActionButton
              kind={workflowAction.kind}
              label={workflowAction.label}
              loading={workflowLoading}
              disabled={saving}
              onAction={onWorkflowAction}
            />
          </div>
          <p className="text-[11px] text-muted-foreground sm:text-right">
            Shortcuts: ⌘/Ctrl+S save · Alt+1–3 documents
          </p>
        </div>
      </div>
    </header>
  );
}
