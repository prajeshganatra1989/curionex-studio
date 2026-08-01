"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus, RotateCcw, Search } from "lucide-react";

import { ProjectCard } from "@/components/projects/project-card";
import { ProjectFormModal } from "@/components/projects/project-form-modal";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { TextInput, TextSelect } from "@/components/ui/field";
import { ApiError } from "@/lib/api/client";
import type { Project } from "@/lib/api/types";
import {
  useArchiveProject,
  useCategories,
  useProjects,
  useTags,
} from "@/lib/projects/hooks";
import { useToast } from "@/components/ui/toast";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";

function ProjectsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true">
      {Array.from({ length: 6 }).map((_, i) => (
        <LoadingSkeleton key={i} className="h-44" />
      ))}
    </div>
  );
}

export function ProjectsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const page = Number(searchParams.get("page") || "1") || 1;
  const status = searchParams.get("status") || "";
  const categoryId = searchParams.get("category_id") || "";
  const tagId = searchParams.get("tag_id") || "";
  const search = searchParams.get("search") || "";

  const [searchInput, setSearchInput] = useState(search);
  const debouncedSearch = useDebouncedValue(searchInput, 350);

  const [createOpen, setCreateOpen] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<Project | null>(null);

  const { data: categories = [] } = useCategories(true);
  const { data: tags = [] } = useTags();
  const archiveMutation = useArchiveProject();

  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  useEffect(() => {
    const next = debouncedSearch.trim();
    if (next === search) return;
    const q = new URLSearchParams(searchParams.toString());
    if (next) q.set("search", next);
    else q.delete("search");
    q.set("page", "1");
    router.replace(`/projects?${q.toString()}`);
  }, [debouncedSearch, search, router, searchParams]);

  const params = useMemo(
    () => ({
      page,
      page_size: 12,
      status: status || undefined,
      category_id: categoryId || undefined,
      tag_id: tagId || undefined,
      search: search.trim() || undefined,
    }),
    [page, status, categoryId, tagId, search],
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useProjects(params);

  function updateQuery(next: Record<string, string | null>) {
    const q = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(next)) {
      if (!value) q.delete(key);
      else q.set(key, value);
    }
    if (!("page" in next)) q.set("page", "1");
    router.replace(`/projects?${q.toString()}`);
  }

  async function confirmArchive() {
    if (!archiveTarget) return;
    try {
      await archiveMutation.mutateAsync(archiveTarget.id);
      toast({ title: "Project archived", tone: "success" });
      setArchiveTarget(null);
    } catch (err) {
      toast({
        title: "Could not archive project",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  const hasFilters = Boolean(status || categoryId || tagId || search);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Create, find, and open the projects that power your Shorts pipeline."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        }
      />

      <div className="mb-5 grid gap-3 rounded-xl border border-border bg-surface p-3 sm:grid-cols-2 lg:grid-cols-5">
        <label className="relative sm:col-span-2 lg:col-span-2">
          <span className="sr-only">Search projects</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <TextInput
            className="pl-9"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or CRX code"
          />
        </label>
        <label>
          <span className="sr-only">Status</span>
          <TextSelect
            value={status}
            onChange={(e) => updateQuery({ status: e.target.value || null })}
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </TextSelect>
        </label>
        <label>
          <span className="sr-only">Category</span>
          <TextSelect
            value={categoryId}
            onChange={(e) =>
              updateQuery({ category_id: e.target.value || null })
            }
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </TextSelect>
        </label>
        <div className="flex gap-2">
          <label className="min-w-0 flex-1">
            <span className="sr-only">Tag</span>
            <TextSelect
              value={tagId}
              onChange={(e) => updateQuery({ tag_id: e.target.value || null })}
            >
              <option value="">All tags</option>
              {tags.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </TextSelect>
          </label>
          <Button
            type="button"
            variant="secondary"
            className="shrink-0 px-3"
            aria-label="Reset filters"
            onClick={() => {
              setSearchInput("");
              router.replace("/projects");
            }}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isLoading ? <ProjectsSkeleton /> : null}

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

      {!isLoading && !isError && items.length === 0 && !hasFilters ? (
        <EmptyState
          title="Create your first Curionex project"
          description="Every remarkable video starts with one strong idea."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              Create Project
            </Button>
          }
        />
      ) : null}

      {!isLoading && !isError && items.length === 0 && hasFilters ? (
        <EmptyState
          title="No projects match these filters"
          description="Try clearing search or filters to see more projects."
          action={
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setSearchInput("");
                router.replace("/projects");
              }}
            >
              Reset filters
            </Button>
          }
        />
      ) : null}

      {!isLoading && !isError && items.length > 0 ? (
        <>
          <div
            className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${isFetching ? "opacity-80" : ""}`}
          >
            {items.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onArchive={setArchiveTarget}
              />
            ))}
          </div>
          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={12}
              total={total}
              onPageChange={(next) => updateQuery({ page: String(next) })}
            />
          </div>
        </>
      ) : null}

      <ProjectFormModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        mode="create"
        onCreated={(project) => router.push(`/projects/${project.id}`)}
      />

      <Modal
        open={Boolean(archiveTarget)}
        onClose={() => setArchiveTarget(null)}
        title="Archive project?"
        description="Archiving preserves scripts, packs, versions, and history. Nothing is permanently deleted."
      >
        <p className="text-sm text-muted-foreground">
          Archive{" "}
          <span className="font-medium text-foreground">
            {archiveTarget?.name}
          </span>
          ?
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setArchiveTarget(null)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            loading={archiveMutation.isPending}
            onClick={() => void confirmArchive()}
          >
            Archive project
          </Button>
        </div>
      </Modal>
    </PageContainer>
  );
}
