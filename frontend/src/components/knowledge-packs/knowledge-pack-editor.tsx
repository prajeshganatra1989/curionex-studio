"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ArrowLeft, ArrowRight, List, Save, Sparkles } from "lucide-react";

import { AiDraftReviewPanel } from "@/components/knowledge-packs/ai-draft-review-panel";
import { GenerateAiDraftDialog } from "@/components/knowledge-packs/generate-ai-draft-dialog";
import { KnowledgePackSection } from "@/components/knowledge-packs/knowledge-pack-section";
import { ProgressSidebar } from "@/components/knowledge-packs/progress-sidebar";
import { SaveIndicator } from "@/components/knowledge-packs/save-indicator";
import { SectionDrawer } from "@/components/knowledge-packs/section-drawer";
import { SectionNavigator } from "@/components/knowledge-packs/section-navigator";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { getKnowledgePack, updateKnowledgePackSection } from "@/lib/api/projects";
import type { KnowledgePackSection as SectionRow } from "@/lib/api/types";
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

function sectionsToDraft(sections: SectionRow[]): DraftMap {
  const draft: DraftMap = {};
  for (const meta of SECTION_ORDER) {
    const match = sections.find((s) => s.section_key === meta.key);
    draft[meta.key] = match?.content ?? "";
  }
  return draft;
}

function sectionsToSavedAt(sections: SectionRow[]): SavedAtMap {
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

function WorkspaceShell({ children }: { children: ReactNode }) {
  return <div className="min-h-full bg-background">{children}</div>;
}

export function KnowledgePackEditor() {
  const params = useParams<{ projectId: string; knowledgePackId: string }>();
  const projectId = params.projectId;
  const knowledgePackId = params.knowledgePackId;
  const router = useRouter();
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
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [justSavedAt, setJustSavedAt] = useState<number | null>(null);
  const [aiDraftDialogOpen, setAiDraftDialogOpen] = useState(false);
  const [aiReviewGenerationId, setAiReviewGenerationId] = useState<string | null>(
    null,
  );

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
    setJustSavedAt(null);
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

  const savedLabel = useMemo(() => {
    if (justSavedAt && Date.now() - justSavedAt < 60_000) return "just now";
    if (!packUpdated) return null;
    return formatRelativeTime(packUpdated);
  }, [justSavedAt, packUpdated]);

  const scrollToSection = useCallback((key: string) => {
    const el = document.getElementById(`section-${key}`);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveKey(key);
    setDrawerOpen(false);
  }, []);

  const onSectionChange = useCallback((key: string, value: string) => {
    setDrafts((prev) => {
      if (prev[key] === value) return prev;
      return { ...prev, [key]: value };
    });
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
        rootMargin: "-18% 0px -55% 0px",
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

    const snapshot = drafts;
    const results = await Promise.all(
      keys.map(async (sectionKey) => {
        try {
          const updated = await updateKnowledgePackSection(
            api,
            knowledgePackId,
            sectionKey,
            { content: snapshot[sectionKey] ?? "" },
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

    // Keep local drafts (never lose text). Only advance baselines for successes.
    setBaseline(nextBaseline);
    setSavedAt(nextSavedAt);
    setErrors((prev) => ({ ...prev, ...nextErrors }));
    setSaving(false);

    void queryClient.invalidateQueries({
      queryKey: knowledgePackKeys.detail(knowledgePackId),
    });

    if (successCount === keys.length) {
      setJustSavedAt(Date.now());
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

  function handleDraftReady(generationId: string) {
    setAiDraftDialogOpen(false);
    setAiReviewGenerationId(generationId);
  }

  async function handleDraftApplied({
    appliedSections,
  }: {
    appliedSections: string[];
  }) {
    setAiReviewGenerationId(null);
    try {
      const fresh = await getKnowledgePack(api, knowledgePackId);
      queryClient.setQueryData(knowledgePackKeys.detail(knowledgePackId), fresh);

      // Only advance drafts/baseline for the sections that were just applied —
      // any unsaved local edits on other sections must be preserved.
      setDrafts((prev) => {
        const next = { ...prev };
        for (const key of appliedSections) {
          const match = fresh.sections.find((s) => s.section_key === key);
          if (match) next[key] = match.content;
        }
        return next;
      });
      setBaseline((prev) => {
        const next = { ...prev };
        for (const key of appliedSections) {
          const match = fresh.sections.find((s) => s.section_key === key);
          if (match) next[key] = match.content;
        }
        return next;
      });
      setSavedAt((prev) => {
        const next = { ...prev };
        for (const key of appliedSections) {
          const match = fresh.sections.find((s) => s.section_key === key);
          if (match) next[key] = match.updated_at;
        }
        return next;
      });
      setErrors((prev) => {
        const next = { ...prev };
        for (const key of appliedSections) delete next[key];
        return next;
      });

      toast({
        title: "AI draft applied",
        description: `${appliedSections.length} section${appliedSections.length === 1 ? "" : "s"} updated. Review before publishing.`,
        tone: "success",
      });
    } catch {
      toast({
        title: "Draft applied, but the pack could not be refreshed",
        description: "Reload the page to see the latest content.",
        tone: "error",
      });
    }
  }

  if (packQuery.isLoading || projectQuery.isLoading) {
    return (
      <WorkspaceShell>
        <div className="px-4 py-8 sm:px-8" data-testid="kp-editor-loading">
          <LoadingSkeleton className="mb-6 h-24" />
          <div className="grid gap-8 lg:grid-cols-[13rem_minmax(0,1fr)_15rem]">
            <LoadingSkeleton className="hidden h-96 lg:block" />
            <LoadingSkeleton className="h-[36rem]" />
            <LoadingSkeleton className="hidden h-96 xl:block" />
          </div>
        </div>
      </WorkspaceShell>
    );
  }

  if (packQuery.isError || !packQuery.data) {
    const status = packQuery.error instanceof ApiError ? packQuery.error.status : 0;
    if (status === 404) {
      return (
        <WorkspaceShell>
          <div className="px-4 py-16 sm:px-8">
            <EmptyState
              title="Knowledge Pack not found"
              description="It may have been archived or you may not have access."
              action={
                <Link
                  href={`/projects/${projectId}`}
                  className="text-sm text-brand-orange underline"
                >
                  Back to Project
                </Link>
              }
            />
          </div>
        </WorkspaceShell>
      );
    }
    if (status === 403) {
      return (
        <WorkspaceShell>
          <div className="px-4 py-16 sm:px-8">
            <EmptyState
              title="Access restricted"
              description="You do not have permission to view this Knowledge Pack."
            />
          </div>
        </WorkspaceShell>
      );
    }
    return (
      <WorkspaceShell>
        <div className="px-4 py-16 sm:px-8">
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
      </WorkspaceShell>
    );
  }

  if (!hydrated) {
    return (
      <WorkspaceShell>
        <div className="px-4 py-8 sm:px-8" data-testid="kp-editor-hydrating">
          <LoadingSkeleton className="mb-6 h-24" />
          <LoadingSkeleton className="h-[36rem]" />
        </div>
      </WorkspaceShell>
    );
  }

  const pack = packQuery.data;
  const project = projectQuery.data;

  return (
    <WorkspaceShell>
      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-[96rem] flex-col gap-4 px-4 py-4 sm:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground lg:hidden"
                aria-label="Open section navigator"
                onClick={() => setDrawerOpen(true)}
              >
                <List className="h-4 w-4" />
              </button>
              <Link
                href={`/projects/${projectId}`}
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
              <StatusBadge status={pack.status} />
            </div>
            <h1 className="mt-1.5 truncate text-2xl font-semibold tracking-tight text-foreground">
              {pack.name}
            </h1>
            <p className="mt-1 truncate text-sm text-muted-foreground">
              {project?.name ?? "Project"}
              {packUpdated ? ` · Updated ${formatRelativeTime(packUpdated)}` : ""}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <SaveIndicator
              saving={saving}
              dirty={isDirty}
              savedLabel={savedLabel}
            />
            <Button
              type="button"
              onClick={() => void saveSections(dirtyKeys)}
              loading={saving}
              disabled={!isDirty || saving}
              aria-label="Save Knowledge Pack"
            >
              <Save className="h-4 w-4" />
              Save
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setAiDraftDialogOpen(true)}
            >
              <Sparkles className="h-4 w-4" />
              Generate AI Draft
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => router.push(`/projects/${projectId}/scripts`)}
            >
              Generate Script
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <SectionDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <SectionNavigator
          sections={SECTION_ORDER}
          contents={drafts}
          activeKey={activeKey}
          onNavigate={scrollToSection}
        />
      </SectionDrawer>

      <div className="mx-auto grid max-w-[96rem] gap-10 px-4 py-8 sm:px-8 lg:grid-cols-[13rem_minmax(0,42rem)] lg:justify-between xl:grid-cols-[13rem_minmax(0,42rem)_15rem]">
        <aside className="hidden lg:block">
          <div className="sticky top-32">
            <p className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Sections
            </p>
            <SectionNavigator
              sections={SECTION_ORDER}
              contents={drafts}
              activeKey={activeKey}
              onNavigate={scrollToSection}
            />
          </div>
        </aside>

        <div className="min-w-0 divide-y divide-border/70">
          {SECTION_ORDER.map((meta) => (
            <KnowledgePackSection
              key={meta.key}
              meta={meta}
              content={drafts[meta.key] ?? ""}
              savedAt={savedAt[meta.key] ?? null}
              dirty={dirtyKeys.includes(meta.key as SectionKey)}
              error={errors[meta.key] ?? null}
              onChange={(value) => onSectionChange(meta.key, value)}
              onRetry={() => void saveSections([meta.key])}
            />
          ))}
        </div>

        <div className="hidden xl:block">
          <div className="sticky top-32">
            <ProgressSidebar sections={SECTION_ORDER} contents={drafts} />
          </div>
        </div>
      </div>

      <GenerateAiDraftDialog
        open={aiDraftDialogOpen}
        onClose={() => setAiDraftDialogOpen(false)}
        projectId={projectId}
        knowledgePackId={knowledgePackId}
        packName={pack.name}
        projectName={project?.name}
        onDraftReady={handleDraftReady}
      />

      <Modal
        open={Boolean(aiReviewGenerationId)}
        onClose={() => setAiReviewGenerationId(null)}
        title="Review AI Draft"
        description="Select which sections to bring into this Knowledge Pack."
        size="lg"
      >
        {aiReviewGenerationId ? (
          <AiDraftReviewPanel
            knowledgePackId={knowledgePackId}
            generationId={aiReviewGenerationId}
            currentSectionContents={drafts}
            onApplied={(result) => void handleDraftApplied(result)}
            onClose={() => setAiReviewGenerationId(null)}
          />
        ) : null}
      </Modal>
    </WorkspaceShell>
  );
}

/** @deprecated Prefer KnowledgePackEditor */
export const KnowledgePackEditorPage = KnowledgePackEditor;
