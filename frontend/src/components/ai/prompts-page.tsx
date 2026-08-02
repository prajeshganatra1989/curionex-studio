"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextArea, TextInput, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { VariableChips } from "@/components/ai/variable-chips";
import { useAiPrompts, useCreateAiPrompt } from "@/lib/ai/hooks";
import { validatePromptVariables } from "@/lib/ai/variables";
import { ApiError } from "@/lib/api/client";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { formatRelativeTime } from "@/lib/utils";

function PromptsSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <LoadingSkeleton key={index} className="h-16" />
      ))}
    </div>
  );
}

export function PromptsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const page = Number(searchParams.get("page") || "1") || 1;
  const status = searchParams.get("status") || "";
  const search = searchParams.get("search") || "";

  const [searchInput, setSearchInput] = useState(search);
  const [createOpen, setCreateOpen] = useState(false);
  const debouncedSearch = useDebouncedValue(searchInput, 350);

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
    router.replace(`/ai/prompts?${q.toString()}`);
  }, [debouncedSearch, search, router, searchParams]);

  const params = useMemo(
    () => ({
      page,
      page_size: 12,
      status: status || undefined,
      search: search.trim() || undefined,
    }),
    [page, status, search],
  );

  const { data, isLoading, isError, error, refetch } = useAiPrompts(params);
  const createPrompt = useCreateAiPrompt();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userTemplate, setUserTemplate] = useState("");
  const [variables, setVariables] = useState<string[]>([]);

  const validation = validatePromptVariables(
    systemPrompt,
    userTemplate,
    variables,
  );

  function updateQuery(next: Record<string, string | null>) {
    const q = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(next)) {
      if (!value) q.delete(key);
      else q.set(key, value);
    }
    if (!("page" in next)) q.set("page", "1");
    router.replace(`/ai/prompts?${q.toString()}`);
  }

  async function handleCreate() {
    if (!name.trim() || !validation.valid) return;
    try {
      const prompt = await createPrompt.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
        purpose: purpose.trim() || null,
        system_prompt: systemPrompt,
        user_template: userTemplate,
        variables,
      });
      setCreateOpen(false);
      toast({ title: "Prompt created", tone: "success" });
      router.push(`/ai/prompts/${prompt.id}`);
    } catch {
      toast({ title: "Unable to create prompt", tone: "error" });
    }
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const restricted =
    isError && error instanceof ApiError && error.status === 403;

  return (
    <PageContainer>
      <PageHeader
        title="Prompt Library"
        description="Reusable prompts with immutable version history."
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            New prompt
          </Button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <TextInput
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search prompts…"
            className="pl-9"
            aria-label="Search prompts"
          />
        </div>
        <TextSelect
          value={status}
          onChange={(event) =>
            updateQuery({ status: event.target.value || null })
          }
          aria-label="Filter by status"
          className="sm:w-44"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </TextSelect>
      </div>

      {isLoading ? <PromptsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You do not have permission to view prompts."
        />
      ) : null}

      {!isLoading && isError && !restricted ? (
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load prompts."
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

      {!isLoading && !isError && items.length === 0 ? (
        <EmptyState
          title="No prompts found"
          description="Create a prompt to get started with versioned templates."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              New prompt
            </Button>
          }
        />
      ) : null}

      {!isLoading && !isError && items.length > 0 ? (
        <>
          <ul
            className="divide-y divide-border rounded-xl border border-border/70 bg-surface/40"
            data-testid="prompts-list"
          >
            {items.map((item) => (
              <li key={item.id}>
                <Link
                  href={`/ai/prompts/${item.id}`}
                  className="flex items-start justify-between gap-3 px-4 py-4 transition hover:bg-surface-hover"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate text-sm font-medium text-foreground">
                        {item.name}
                      </p>
                      <StatusBadge status={item.status} />
                    </div>
                    {item.description ? (
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                        {item.description}
                      </p>
                    ) : null}
                    <p className="mt-1 text-xs text-muted-foreground">
                      Updated{" "}
                      <time dateTime={item.updated_at}>
                        {formatRelativeTime(item.updated_at)}
                      </time>
                    </p>
                  </div>
                  {item.active_version ? (
                    <span className="shrink-0 text-xs text-muted-foreground">
                      v{item.active_version.version_number}
                    </span>
                  ) : null}
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <Pagination
              page={page}
              pageSize={params.page_size ?? 12}
              total={total}
              onPageChange={(nextPage) =>
                updateQuery({ page: String(nextPage) })
              }
            />
          </div>
        </>
      ) : null}

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New prompt"
        description="Creates the prompt and an initial version."
        size="lg"
      >
        <div className="space-y-4">
          <Field label="Name" htmlFor="prompt-name">
            <TextInput
              id="prompt-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </Field>
          <Field label="Description" htmlFor="prompt-description">
            <TextInput
              id="prompt-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </Field>
          <Field label="Purpose" htmlFor="prompt-purpose">
            <TextInput
              id="prompt-purpose"
              value={purpose}
              onChange={(event) => setPurpose(event.target.value)}
            />
          </Field>
          <Field label="System prompt" htmlFor="prompt-system">
            <TextArea
              id="prompt-system"
              value={systemPrompt}
              onChange={(event) => setSystemPrompt(event.target.value)}
              className="min-h-28 font-mono text-xs"
            />
          </Field>
          <Field label="User template" htmlFor="prompt-user">
            <TextArea
              id="prompt-user"
              value={userTemplate}
              onChange={(event) => setUserTemplate(event.target.value)}
              className="min-h-28 font-mono text-xs"
            />
          </Field>
          <Field label="Variables" htmlFor="prompt-variables">
            <VariableChips
              variables={variables}
              onChange={setVariables}
              errors={validation.valid ? undefined : validation.errors}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              loading={createPrompt.isPending}
              disabled={!name.trim() || !validation.valid}
              onClick={() => void handleCreate()}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}
