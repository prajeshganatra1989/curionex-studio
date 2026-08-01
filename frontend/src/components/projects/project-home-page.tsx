"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import {
  Archive,
  BookOpen,
  FileText,
  Layers3,
  Pencil,
  Workflow,
} from "lucide-react";

import {
  CreateKnowledgePackModal,
  CreateScriptModal,
} from "@/components/projects/quick-create-modals";
import { ProjectFormModal } from "@/components/projects/project-form-modal";
import { PageContainer } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { SectionPanel } from "@/components/ui/section-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import {
  useArchiveProject,
  useProject,
  useProjectKnowledgePacks,
  useProjectScripts,
  useProjectVersions,
  useScriptWorkflowStatus,
} from "@/lib/projects/hooks";
import { cn, formatRelativeTime } from "@/lib/utils";

const TABS = [
  { id: "overview", label: "Overview", href: "" },
  { id: "packs", label: "Knowledge Packs", href: "packs" },
  { id: "scripts", label: "Scripts", href: "scripts" },
  { id: "versions", label: "Versions", href: "versions" },
  { id: "workflow", label: "Workflow", href: "workflow" },
  { id: "activity", label: "Activity", href: "activity" },
] as const;

export function ProjectHomePage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { toast } = useToast();

  const { data: project, isLoading, isError, error, refetch } =
    useProject(projectId);
  const packs = useProjectKnowledgePacks(projectId);
  const scripts = useProjectScripts(projectId);
  const versions = useProjectVersions(projectId);
  const latestScriptId = scripts.data?.items[0]?.id ?? null;
  const workflow = useScriptWorkflowStatus(latestScriptId);

  const [editOpen, setEditOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [packOpen, setPackOpen] = useState(false);
  const [scriptOpen, setScriptOpen] = useState(false);
  const archiveMutation = useArchiveProject();

  if (isLoading) {
    return (
      <PageContainer>
        <LoadingSkeleton className="mb-4 h-28" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-40" />
          ))}
        </div>
      </PageContainer>
    );
  }

  if (isError || !project) {
    const status = error instanceof ApiError ? error.status : 0;
    if (status === 404) {
      return (
        <PageContainer>
          <EmptyState
            title="Project not found"
            description="This project may have been removed or you may not have access."
            action={
              <Link href="/projects" className="text-sm text-brand-orange underline">
                Back to projects
              </Link>
            }
          />
        </PageContainer>
      );
    }
    if (status === 403) {
      return (
        <PageContainer>
          <EmptyState
            title="Access restricted"
            description="You do not have permission to view this project."
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer>
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load project."
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
      </PageContainer>
    );
  }

  async function confirmArchive() {
    try {
      await archiveMutation.mutateAsync(projectId);
      toast({ title: "Project archived", tone: "success" });
      setArchiveOpen(false);
      void refetch();
    } catch (err) {
      toast({
        title: "Could not archive project",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <p className="font-mono text-sm text-brand-amber">
            {project.project_code}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              {project.name}
            </h1>
            <StatusBadge status={project.status} />
          </div>
          {project.description ? (
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              {project.description}
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
            {project.category ? (
              <span className="rounded-md border border-border px-2 py-0.5">
                {project.category.name}
              </span>
            ) : null}
            {project.tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-md border border-border px-2 py-0.5"
              >
                {tag.name}
              </span>
            ))}
            <span>Updated {formatRelativeTime(project.updated_at)}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => setEditOpen(true)}>
            <Pencil className="h-4 w-4" />
            Edit
          </Button>
          {project.status !== "archived" ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => setArchiveOpen(true)}
            >
              <Archive className="h-4 w-4" />
              Archive
            </Button>
          ) : null}
        </div>
      </div>

      <nav
        aria-label="Project sections"
        className="mb-5 flex gap-1 overflow-x-auto border-b border-border pb-px"
      >
        {TABS.map((tab) => {
          const href =
            tab.id === "overview"
              ? `/projects/${projectId}`
              : `/projects/${projectId}/${tab.href}`;
          const active = tab.id === "overview";
          return (
            <Link
              key={tab.id}
              href={href}
              className={cn(
                "whitespace-nowrap rounded-t-md px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground",
                active &&
                  "border-b-2 border-brand-orange text-foreground",
              )}
              aria-current={active ? "page" : undefined}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>

      <div className="mb-4 flex flex-wrap gap-2">
        <Button type="button" onClick={() => setPackOpen(true)}>
          <BookOpen className="h-4 w-4" />
          Create Knowledge Pack
        </Button>
        <Button type="button" variant="secondary" onClick={() => setScriptOpen(true)}>
          <FileText className="h-4 w-4" />
          Create Script
        </Button>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <SectionPanel
          title="Knowledge Packs"
          action={
            <button
              type="button"
              className="text-xs text-brand-orange hover:underline"
              onClick={() => setPackOpen(true)}
            >
              Create
            </button>
          }
        >
          {packs.isLoading ? (
            <LoadingSkeleton className="h-20" />
          ) : packs.data && packs.data.total > 0 ? (
            <div className="space-y-2">
              <p className="text-2xl font-semibold tabular-nums">
                {packs.data.total}
              </p>
              <ul className="space-y-2">
                {packs.data.items.slice(0, 3).map((pack) => (
                  <li key={pack.id}>
                    <Link
                      href={`/projects/${projectId}/knowledge-packs/${pack.id}`}
                      className="flex items-center justify-between gap-2 rounded-md px-2 py-2 text-sm hover:bg-surface-hover"
                    >
                      <span className="truncate">{pack.name}</span>
                      <StatusBadge status={pack.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState
              title="No Knowledge Packs yet"
              description="Capture research context before scripting."
            />
          )}
        </SectionPanel>

        <SectionPanel
          title="Scripts"
          action={
            <button
              type="button"
              className="text-xs text-brand-orange hover:underline"
              onClick={() => setScriptOpen(true)}
            >
              Create
            </button>
          }
        >
          {scripts.isLoading ? (
            <LoadingSkeleton className="h-20" />
          ) : scripts.data && scripts.data.total > 0 ? (
            <div className="space-y-2">
              <p className="text-2xl font-semibold tabular-nums">
                {scripts.data.total}
              </p>
              <ul className="space-y-2">
                {scripts.data.items.slice(0, 3).map((script) => (
                  <li
                    key={script.id}
                    className="flex items-center justify-between gap-2 rounded-md px-2 py-2 text-sm hover:bg-surface-hover"
                  >
                    <span className="min-w-0 truncate">
                      <span className="font-mono text-[11px] text-brand-amber">
                        {script.script_code}
                      </span>{" "}
                      {script.title}
                    </span>
                    <StatusBadge status={script.status} />
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState
              title="No scripts yet"
              description="Create a script workspace to start Discovery Brief → Story Spine → Master Script."
            />
          )}
        </SectionPanel>

        <SectionPanel title="Versions">
          {versions.isLoading ? (
            <LoadingSkeleton className="h-20" />
          ) : (
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <Layers3 className="h-4 w-4 text-brand-orange" />
                <span className="text-muted-foreground">Latest</span>
                <span className="ml-auto">
                  {versions.data?.latest
                    ? `v${versions.data.latest.version_number} · ${versions.data.latest.status}`
                    : "Not available yet"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Layers3 className="h-4 w-4 text-success" />
                <span className="text-muted-foreground">Approved</span>
                <span className="ml-auto">
                  {versions.data?.approved
                    ? `v${versions.data.approved.version_number}`
                    : "Not available yet"}
                </span>
              </div>
            </div>
          )}
        </SectionPanel>

        <SectionPanel title="Workflow">
          {!latestScriptId ? (
            <EmptyState
              title="No workflow yet"
              description="Create a script to start the content production workflow."
            />
          ) : workflow.isLoading ? (
            <LoadingSkeleton className="h-20" />
          ) : workflow.isError ? (
            <p className="text-sm text-muted-foreground">
              Workflow summary not available yet.
            </p>
          ) : workflow.data ? (
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Workflow className="h-4 w-4 text-brand-orange" />
                <span>Stage</span>
                <StatusBadge className="ml-auto" status={workflow.data.stage} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Status</span>
                <StatusBadge status={workflow.data.status} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Active version</span>
                <span>
                  {workflow.data.active_version
                    ? `v${workflow.data.active_version.version_number}`
                    : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Pending review</span>
                <span>
                  {workflow.data.pending_approval ? "Yes" : "No"}
                </span>
              </div>
            </div>
          ) : null}
        </SectionPanel>
      </div>

      <div className="mt-4">
        <SectionPanel title="Recent Activity">
          <EmptyState
            title="Activity unavailable"
            description="Project-scoped activity requires audit.view and efficient project filtering. Coming in a later sprint."
          />
        </SectionPanel>
      </div>

      <ProjectFormModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        mode="edit"
        project={project}
      />
      <CreateKnowledgePackModal
        open={packOpen}
        onClose={() => setPackOpen(false)}
        projectId={projectId}
      />
      <CreateScriptModal
        open={scriptOpen}
        onClose={() => setScriptOpen(false)}
        projectId={projectId}
      />
      <Modal
        open={archiveOpen}
        onClose={() => setArchiveOpen(false)}
        title="Archive project?"
        description="Archiving preserves content. You can still find it with the archived filter."
      >
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => setArchiveOpen(false)}>
            Cancel
          </Button>
          <Button
            type="button"
            loading={archiveMutation.isPending}
            onClick={() => void confirmArchive()}
          >
            Archive
          </Button>
        </div>
      </Modal>
    </PageContainer>
  );
}

export function ProjectSectionPlaceholder({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  const params = useParams<{ projectId: string }>();
  return (
    <PageContainer>
      <EmptyState
        title={title}
        description={description}
        action={
          <Link
            href={`/projects/${params.projectId}`}
            className="text-sm text-brand-orange hover:underline"
          >
            Back to overview
          </Link>
        }
      />
    </PageContainer>
  );
}
