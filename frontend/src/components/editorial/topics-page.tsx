"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ExternalLink, FolderPlus, Search } from "lucide-react";

import { CreateProjectFromTopicModal } from "@/components/editorial/create-project-from-topic-modal";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge } from "@/components/ui/status-badge";
import { TextInput, TextSelect } from "@/components/ui/field";
import { ApiError } from "@/lib/api/client";
import {
  EDITORIAL_CATEGORIES,
  PRODUCTION_WAVES,
  TOPIC_DIFFICULTIES,
  TOPIC_PRIORITIES,
  TOPIC_STATUSES,
  type EditorialTopic,
} from "@/lib/editorial/types";
import { useEditorialTopics } from "@/lib/editorial/hooks";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";

const PAGE_SIZE = 20;

function TopicsSkeleton() {
  return (
    <div className="space-y-2" aria-busy="true">
      {Array.from({ length: 8 }).map((_, i) => (
        <LoadingSkeleton key={i} className="h-14" />
      ))}
    </div>
  );
}

export function TopicsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1") || 1;
  const status = searchParams.get("status") || "";
  const category = searchParams.get("category") || "";
  const difficulty = searchParams.get("difficulty") || "";
  const priority = searchParams.get("priority") || "";
  const wave = searchParams.get("production_wave") || "";
  const minEvergreen = searchParams.get("min_evergreen_score") || "";
  const sort = searchParams.get("sort") || "updated_at_desc";
  const search = searchParams.get("search") || "";

  const [searchInput, setSearchInput] = useState(search);
  const debouncedSearch = useDebouncedValue(searchInput, 350);
  const [createTopic, setCreateTopic] = useState<EditorialTopic | null>(null);

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
    router.replace(`/topics?${q.toString()}`);
  }, [debouncedSearch, search, router, searchParams]);

  const params = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      status: status || undefined,
      category: category || undefined,
      difficulty: difficulty || undefined,
      priority: priority || undefined,
      production_wave: wave ? Number(wave) : undefined,
      min_evergreen_score: minEvergreen ? Number(minEvergreen) : undefined,
      search: search.trim() || undefined,
      sort,
    }),
    [page, status, category, difficulty, priority, wave, minEvergreen, search, sort],
  );

  const { data, isLoading, isError, error, refetch } = useEditorialTopics(params);

  function updateParam(key: string, value: string) {
    const q = new URLSearchParams(searchParams.toString());
    if (value) q.set(key, value);
    else q.delete(key);
    q.set("page", "1");
    router.replace(`/topics?${q.toString()}`);
  }

  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Editorial Library"
        description="Plan and select evergreen YouTube Shorts ideas. Create a project when a topic is ready."
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="relative sm:col-span-2 lg:col-span-2">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <TextInput
            aria-label="Search topics"
            className="pl-9"
            placeholder="Search title, notes, slug…"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </div>
        <TextSelect
          aria-label="Filter by category"
          value={category}
          onChange={(event) => updateParam("category", event.target.value)}
        >
          <option value="">All categories</option>
          {EDITORIAL_CATEGORIES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </TextSelect>
        <TextSelect
          aria-label="Filter by status"
          value={status}
          onChange={(event) => updateParam("status", event.target.value)}
        >
          <option value="">All statuses</option>
          {TOPIC_STATUSES.map((item) => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </TextSelect>
        <TextSelect
          aria-label="Filter by difficulty"
          value={difficulty}
          onChange={(event) => updateParam("difficulty", event.target.value)}
        >
          <option value="">All difficulties</option>
          {TOPIC_DIFFICULTIES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </TextSelect>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <TextSelect
          aria-label="Filter by priority"
          value={priority}
          onChange={(event) => updateParam("priority", event.target.value)}
        >
          <option value="">All priorities</option>
          {TOPIC_PRIORITIES.map((item) => (
            <option key={item} value={item}>
              Tier {item}
            </option>
          ))}
        </TextSelect>
        <TextSelect
          aria-label="Filter by production wave"
          value={wave}
          onChange={(event) => updateParam("production_wave", event.target.value)}
        >
          <option value="">All waves</option>
          {PRODUCTION_WAVES.map((item) => (
            <option key={item} value={String(item)}>
              Wave {item}
            </option>
          ))}
        </TextSelect>
        <TextSelect
          aria-label="Minimum evergreen score"
          value={minEvergreen}
          onChange={(event) =>
            updateParam("min_evergreen_score", event.target.value)
          }
        >
          <option value="">Any evergreen score</option>
          <option value="60">60+</option>
          <option value="70">70+</option>
          <option value="80">80+</option>
          <option value="90">90+</option>
        </TextSelect>
        <TextSelect
          aria-label="Sort topics"
          value={sort}
          onChange={(event) => updateParam("sort", event.target.value)}
        >
          <option value="updated_at_desc">Recently updated</option>
          <option value="evergreen_desc">Evergreen score</option>
          <option value="curiosity_desc">Curiosity score</option>
          <option value="priority_asc">Priority A–C</option>
          <option value="wave_asc">Wave 1–4</option>
          <option value="title_asc">Title A–Z</option>
          <option value="created_at_desc">Newest</option>
        </TextSelect>
      </div>

      {isLoading ? <TopicsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Topics restricted"
          description="You need editorial_topics.view to browse the Editorial Library."
        />
      ) : null}

      {isError && !restricted ? (
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load topics."
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

      {!isLoading && !isError && data && data.items.length === 0 ? (
        <EmptyState
          title="No topics match"
          description="Adjust filters or seed the evergreen catalog to get started."
        />
      ) : null}

      {!isLoading && !isError && data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-elevated text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Priority</th>
                  <th className="px-4 py-3 font-medium">Wave</th>
                  <th className="px-4 py-3 font-medium">Evergreen</th>
                  <th className="px-4 py-3 font-medium">Curiosity</th>
                  <th className="px-4 py-3 font-medium">Difficulty</th>
                  <th className="px-4 py-3 font-medium">Linked Project</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((topic) => (
                  <tr key={topic.id} className="hover:bg-surface-hover/60">
                    <td className="max-w-xs px-4 py-3">
                      <div className="font-medium text-foreground">
                        {topic.title}
                      </div>
                      {topic.is_featured ? (
                        <span className="mt-1 inline-block text-[10px] uppercase tracking-wide text-brand-amber">
                          Featured
                        </span>
                      ) : null}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {topic.category}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={topic.status} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-md border border-border px-1.5 py-0.5 text-[11px] font-semibold tracking-wide">
                        {topic.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-muted-foreground">
                      {topic.production_wave}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{topic.evergreen_score}</td>
                    <td className="px-4 py-3 tabular-nums">{topic.curiosity_score}</td>
                    <td className="px-4 py-3 capitalize">{topic.difficulty}</td>
                    <td className="px-4 py-3">
                      {topic.linked_project ? (
                        <Link
                          href={`/projects/${topic.linked_project.id}`}
                          className="font-mono text-xs text-brand-amber hover:underline"
                        >
                          {topic.linked_project.project_code}
                        </Link>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        {topic.linked_project_id ? (
                          <Link
                            href={`/projects/${topic.linked_project_id}`}
                            className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs hover:bg-surface-elevated"
                          >
                            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                            Open
                          </Link>
                        ) : (
                          <Button
                            type="button"
                            variant="secondary"
                            className="h-8 px-2 text-xs"
                            onClick={() => setCreateTopic(topic)}
                          >
                            <FolderPlus className="h-3.5 w-3.5" aria-hidden />
                            Start Production
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4">
            <Pagination
              page={data.page}
              pageSize={data.page_size}
              total={data.total}
              onPageChange={(nextPage) => {
                const q = new URLSearchParams(searchParams.toString());
                q.set("page", String(nextPage));
                router.replace(`/topics?${q.toString()}`);
              }}
            />
          </div>
        </>
      ) : null}

      <CreateProjectFromTopicModal
        open={Boolean(createTopic)}
        topic={createTopic}
        onClose={() => setCreateTopic(null)}
        onCreated={() => {
          void router.push("/production/session");
        }}
      />
    </PageContainer>
  );
}
