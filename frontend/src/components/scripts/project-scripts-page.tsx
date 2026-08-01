"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { Archive, FileText, Plus } from "lucide-react";

import { CreateScriptModal } from "@/components/projects/quick-create-modals";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { TextInput, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import {
  useArchiveScript,
  useProjectScripts,
  useScriptWorkflowStatus,
} from "@/lib/scripts/hooks";
import { useProjectKnowledgePacks } from "@/lib/projects/hooks";
import { formatRelativeTime } from "@/lib/utils";

function ScriptWorkflowStage({ scriptId }: { scriptId: string }) {
  const { data, isLoading } = useScriptWorkflowStatus(scriptId);
  if (isLoading) return <span className="text-muted-foreground">…</span>;
  if (!data) return <span className="text-muted-foreground">—</span>;
  return <StatusBadge status={data.stage} />;
}

export function ProjectScriptsPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { toast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const scriptsQuery = useProjectScripts(projectId, {
    page,
    page_size: 20,
    status: status || undefined,
    search: search || undefined,
  });
  const packsQuery = useProjectKnowledgePacks(projectId, {
    page: 1,
    page_size: 100,
  });
  const archiveScript = useArchiveScript(projectId);

  const packNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const pack of packsQuery.data?.items ?? []) {
      map.set(pack.id, pack.name);
    }
    return map;
  }, [packsQuery.data]);

  async function onArchive(scriptId: string, title: string) {
    if (!window.confirm(`Archive “${title}”?`)) return;
    try {
      await archiveScript.mutateAsync(scriptId);
      toast({ title: "Script archived", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not archive script",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Scripts"
        description="Open a workspace to write Discovery Brief, Story Spine, and Master Script."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            New Script
          </Button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <form
          className="flex flex-1 gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setSearch(searchInput.trim());
          }}
        >
          <TextInput
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search title or code"
            aria-label="Search scripts"
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
        <TextSelect
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value);
          }}
          aria-label="Filter by status"
          className="sm:w-48"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="in_progress">In progress</option>
          <option value="in_review">In review</option>
          <option value="approved">Approved</option>
          <option value="archived">Archived</option>
        </TextSelect>
      </div>

      {scriptsQuery.isLoading ? (
        <div className="space-y-3" data-testid="scripts-loading">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-20" />
          ))}
        </div>
      ) : null}

      {scriptsQuery.isError ? (
        <ErrorState
          message={
            scriptsQuery.error instanceof ApiError
              ? scriptsQuery.error.detail
              : "Unable to load scripts."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void scriptsQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      ) : null}

      {!scriptsQuery.isLoading &&
      !scriptsQuery.isError &&
      (scriptsQuery.data?.items.length ?? 0) === 0 ? (
        <EmptyState
          title="No scripts yet"
          description="Create a script to open the production workspace."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              New Script
            </Button>
          }
        />
      ) : null}

      {!scriptsQuery.isLoading &&
      !scriptsQuery.isError &&
      scriptsQuery.data &&
      scriptsQuery.data.items.length > 0 ? (
        <>
          <div className="hidden overflow-x-auto rounded-xl border border-border md:block">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-border bg-surface/80 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Code</th>
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Knowledge Pack</th>
                  <th className="px-4 py-3 font-medium">Workflow</th>
                  <th className="px-4 py-3 font-medium">Updated</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-surface">
                {scriptsQuery.data.items.map((script) => (
                  <tr key={script.id}>
                    <td className="px-4 py-3 font-mono text-xs text-brand-amber">
                      {script.script_code}
                    </td>
                    <td className="px-4 py-3 font-medium text-foreground">
                      {script.title}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={script.status} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {script.knowledge_pack_id
                        ? (packNameById.get(script.knowledge_pack_id) ?? "Linked")
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <ScriptWorkflowStage scriptId={script.id} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatRelativeTime(script.updated_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Link
                          href={`/projects/${projectId}/scripts/${script.id}`}
                          className="text-sm text-brand-orange underline-offset-2 hover:underline"
                        >
                          Open Workspace
                        </Link>
                        {script.status !== "archived" ? (
                          <button
                            type="button"
                            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
                            onClick={() =>
                              void onArchive(script.id, script.title)
                            }
                            aria-label={`Archive ${script.title}`}
                          >
                            <Archive className="h-3.5 w-3.5" />
                            Archive
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="space-y-3 md:hidden" data-testid="scripts-mobile-list">
            {scriptsQuery.data.items.map((script) => (
              <li
                key={script.id}
                className="rounded-xl border border-border bg-surface p-4"
              >
                <div className="flex items-start gap-3">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border text-brand-orange">
                    <FileText className="h-5 w-5" aria-hidden />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-brand-amber">
                        {script.script_code}
                      </span>
                      <StatusBadge status={script.status} />
                    </div>
                    <p className="mt-1 font-medium text-foreground">
                      {script.title}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {script.knowledge_pack_id
                        ? (packNameById.get(script.knowledge_pack_id) ??
                          "Knowledge Pack")
                        : "No Knowledge Pack"}
                      {" · "}
                      Updated {formatRelativeTime(script.updated_at)}
                    </p>
                    <div className="mt-2">
                      <ScriptWorkflowStage scriptId={script.id} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-3">
                      <Link
                        href={`/projects/${projectId}/scripts/${script.id}`}
                        className="text-sm text-brand-orange underline"
                      >
                        Open Workspace
                      </Link>
                      {script.status !== "archived" ? (
                        <button
                          type="button"
                          className="text-sm text-muted-foreground"
                          onClick={() => void onArchive(script.id, script.title)}
                        >
                          Archive
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4">
            <Pagination
              page={scriptsQuery.data.page}
              pageSize={scriptsQuery.data.page_size}
              total={scriptsQuery.data.total}
              onPageChange={setPage}
            />
          </div>
        </>
      ) : null}

      <CreateScriptModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        projectId={projectId}
      />
    </PageContainer>
  );
}
