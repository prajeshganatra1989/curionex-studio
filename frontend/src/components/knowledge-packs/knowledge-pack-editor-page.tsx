"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { ArrowLeft, Save } from "lucide-react";

import { ProgressPanel } from "@/components/knowledge-packs/progress-panel";
import { SectionEditor } from "@/components/knowledge-packs/section-editor";
import { SectionNav } from "@/components/knowledge-packs/section-nav";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import {
  updateKnowledgePackSection,
} from "@/lib/api/projects";
import type { KnowledgePackSection } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/auth-context";
import {
  knowledgePackKeys,
  useKnowledgePack,
} from "@/lib/knowledge-packs/hooks";
import { SECTION_ORDER, type SectionKey } from "@/lib/knowledge-packs/sections";
import { useProject } from "@/lib/projects/hooks";
import { formatRelativeTime } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";

type DraftMap = Record<string, string>;
type SavedAtMap = Record<string, string>;
type ErrorMap = Record<string, string>;

function sectionsToDraft(sections: KnowledgePackSection[]): DraftMap {
  const draft: DraftMap = {};
  for (const meta of SECTION_ORDER) {
    const match = sections.find((s) => s.section_key === meta.key);
    draft[meta.key] = match?.content ?? "";
  }
  return draft;
}

function sectionsToSavedAt(sections: KnowledgePackSection[]): SavedAtMap {
  const map: SavedAtMap = {};
  for (const meta of SECTION_ORDER) {
    const match = sections.find((s) => s.section_key === meta.key);
    if (match) map[meta.key] = match.updated_at;
  }
  return map;
}

function latestTimestamp(map: SavedAtMap): string | null {
  const values = Object.values(map);
  if (values.length === 0) return null;
  return values.reduce((latest, iso) =>
    new Date(iso).getTime() > new Date(latest).getTime() ? iso : latest,
  );
}

export function KnowledgePackEditorPage() {
  const params = useParams<{ projectId: string; knowledgePackId: string }>();
  const projectId = params.projectId;
  const knowledgePackId = params.knowledgePackId;
  const { api } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const projectQuery = useProject(projectId);
  const packQuery = useKnowledgePack(knowledgePackId);

  const [drafts, setDrafts] = useState<DraftMap>({});
  const [baseline, setBaseline] = useState<DraftMap>({});
  const [savedAt, setSavedAt] = useState<SavedAtMap>({});
  const [errors, setErrors] = useState<ErrorMap>({});
  const [activeKey, setActiveKey] = useState<string>(SECTION_ORDER[0]!.key);
  const [saving, setSaving] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const scrollRootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!packQuery.data || hydrated) return;
    const nextDraft = sectionsToDraft(packQuery.data.sections);
    setDrafts(nextDraft);
    setBaseline(nextDraft);
    setSavedAt(sectionsToSavedAt(packQuery.data.sections));
    setHydrated(true);
  }, [packQuery.data, hydrated]);

  useEffect(() => {
    setHydrated(false);
  }, [knowledgePackId]);

  const dirtyKeys = useMemo(
    () =>
      SECTION_ORDER.map((s) => s.key).filter(
        (key) => (drafts[key] ?? "") !== (baseline[key] ?? ""),
      ),
    [drafts, baseline],
  );
  const isDirty = dirtyKeys.length > 0;
  const packUpdated = latestTimestamp(savedAt) ?? packQuery.data?.updated_at ?? null;

  const saveStatusLabel = saving
    ? "Saving..."
    : isDirty
      ? "Unsaved changes"
      : packUpdated
        ? `Saved ${formatRelativeTime(packUpdated)}`
        : "Saved";

  const scrollToSection = useCallback((key: string) => {
    const el = document.getElementById(`section-${key}`);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveKey(key);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    const nodes = SECTION_ORDER.map((s) =>
      document.getElementById(`section-${s.key}`),
    ).filter((n): n is HTMLElement => Boolean(n));
    if (nodes.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        const top = visible[0];
        if (!top) return;
        const key = (top.target as HTMLElement).dataset.sectionKey;
        if (key) setActiveKey(key);
      },
      {
        root: null,
        rootMargin: "-20% 0px -55% 0px",
        threshold: [0.1, 0.25, 0.5],
      },
    );

    for (const node of nodes) observer.observe(node);
    return () => observer.disconnect();
  }, [hydrated, knowledgePackId]);

  async function saveSections(keys: string[]) {
    if (keys.length === 0 || saving) return;
    setSaving(true);
    setErrors((prev) => {
      const next = { ...prev };
      for (const key of keys) delete next[key];
      return next;
    });

    const results = await Promise.all(
      keys.map(async (sectionKey) => {
        try {
          const updated = await updateKnowledgePackSection(
            api,
            knowledgePackId,
            sectionKey,
            { content: drafts[sectionKey] ?? "" },
          );
          return { sectionKey, ok: true as const, updated };
        } catch (err) {
          const detail =
            err instanceof ApiError ? err.detail : "Could not save section.";
          return { sectionKey, ok: false as const, detail };
        }
      }),
    );

    const nextBaseline = { ...baseline };
    const nextSavedAt = { ...savedAt };
    const nextErrors: ErrorMap = {};
    let successCount = 0;

    for (const result of results) {
      if (result.ok) {
        successCount += 1;
        nextBaseline[result.sectionKey] = result.updated.content;
        nextSavedAt[result.sectionKey] = result.updated.updated_at;
      } else {
        nextErrors[result.sectionKey] = result.detail;
      }
    }

    setBaseline(nextBaseline);
    setSavedAt(nextSavedAt);
    setErrors((prev) => ({ ...prev, ...nextErrors }));
    setSaving(false);

    void queryClient.invalidateQueries({
      queryKey: knowledgePackKeys.detail(knowledgePackId),
    });

    if (successCount === keys.length) {
      toast({ title: "Knowledge Pack saved", tone: "success" });
    } else if (successCount > 0) {
      toast({
        title: "Some sections failed to save",
        description: "Your local edits are preserved. Retry failed sections.",
        tone: "error",
      });
    } else {
      toast({
        title: "Save failed",
        description: "Your local edits are preserved. Try again.",
        tone: "error",
      });
    }
  }

  async function handleSave() {
    await saveSections(dirtyKeys);
  }

  async function handleRetry(sectionKey: string) {
    await saveSections([sectionKey]);
  }

  if (packQuery.isLoading || projectQuery.isLoading) {
    return (
      <div className="px-4 py-6 sm:px-6" data-testid="kp-editor-loading">
        <LoadingSkeleton className="mb-4 h-20" />
        <div className="grid gap-4 lg:grid-cols-[14rem_minmax(0,1fr)_16rem]">
          <LoadingSkeleton className="hidden h-80 lg:block" />
          <LoadingSkeleton className="h-[32rem]" />
          <LoadingSkeleton className="hidden h-80 xl:block" />
        </div>
      </div>
    );
  }

  if (packQuery.isError || !packQuery.data) {
    const status = packQuery.error instanceof ApiError ? packQuery.error.status : 0;
    if (status === 404) {
      return (
        <div className="px-4 py-10 sm:px-6">
          <EmptyState
            title="Knowledge Pack not found"
            description="It may have been archived or you may not have access."
            action={
              <Link
                href={`/projects/${projectId}`}
                className="text-sm text-brand-orange underline"
              >
                Back to project
              </Link>
            }
          />
        </div>
      );
    }
    if (status === 403) {
      return (
        <div className="px-4 py-10 sm:px-6">
          <EmptyState
            title="Access restricted"
            description="You do not have permission to view this Knowledge Pack."
          />
        </div>
      );
    }
    return (
      <div className="px-4 py-10 sm:px-6">
        <ErrorState
          message={
            packQuery.error instanceof ApiError
              ? packQuery.error.detail
              : "Unable to load Knowledge Pack."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void packQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      </div>
    );
  }

  if (!hydrated) {
    return (
      <div className="px-4 py-6 sm:px-6" data-testid="kp-editor-hydrating">
        <LoadingSkeleton className="mb-4 h-20" />
        <LoadingSkeleton className="h-[32rem]" />
      </div>
    );
  }

  const pack = packQuery.data;
  const project = projectQuery.data;

  return (
    <div ref={scrollRootRef} className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="mb-1 flex items-center gap-2">
              <Link
                href={`/projects/${projectId}`}
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Project
              </Link>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {project ? (
                <span className="font-mono text-xs text-brand-amber">
                  {project.project_code}
                </span>
              ) : null}
              <StatusBadge status={pack.status} />
            </div>
            <h1 className="mt-1 truncate text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
              {pack.name}
            </h1>
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {project?.name ?? "Project"}
              {packUpdated ? ` · Updated ${formatRelativeTime(packUpdated)}` : ""}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <p
              className="text-sm text-muted-foreground"
              aria-live="polite"
              data-testid="save-status"
            >
              {saveStatusLabel}
            </p>
            <Button
              type="button"
              onClick={() => void handleSave()}
              loading={saving}
              disabled={!isDirty || saving}
              aria-label="Save Knowledge Pack"
            >
              <Save className="h-4 w-4" />
              Save
            </Button>
          </div>
        </div>

        <div className="border-t border-border px-4 py-2 lg:hidden sm:px-6">
          <SectionNav
            sections={SECTION_ORDER}
            contents={drafts}
            activeKey={activeKey}
            onNavigate={scrollToSection}
            orientation="horizontal"
          />
        </div>
      </header>

      <div className="mx-auto grid max-w-[90rem] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[14rem_minmax(0,1fr)] xl:grid-cols-[14rem_minmax(0,1fr)_16rem]">
        <aside className="hidden lg:block">
          <div className="sticky top-28">
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Sections
            </p>
            <SectionNav
              sections={SECTION_ORDER}
              contents={drafts}
              activeKey={activeKey}
              onNavigate={scrollToSection}
            />
          </div>
        </aside>

        <div className="min-w-0">
          {SECTION_ORDER.map((meta) => (
            <SectionEditor
              key={meta.key}
              meta={meta}
              content={drafts[meta.key] ?? ""}
              savedAt={savedAt[meta.key] ?? null}
              dirty={dirtyKeys.includes(meta.key as SectionKey)}
              error={errors[meta.key] ?? null}
              onChange={(value) =>
                setDrafts((prev) => ({ ...prev, [meta.key]: value }))
              }
              onRetry={() => void handleRetry(meta.key)}
            />
          ))}
        </div>

        <div className="hidden xl:block">
          <div className="sticky top-28">
            <ProgressPanel sections={SECTION_ORDER} contents={drafts} />
          </div>
        </div>
      </div>
    </div>
  );
}
