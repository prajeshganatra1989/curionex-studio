"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { SectionDrawer } from "@/components/knowledge-packs/section-drawer";
import { GenerateScriptAiDraftDialog } from "@/components/scripts/generate-script-ai-draft-dialog";
import { KnowledgePackContextPanel } from "@/components/scripts/knowledge-pack-context-panel";
import { ReviewScriptQualityDialog } from "@/components/scripts/review-script-quality-dialog";
import { ScriptAiDraftReviewPanel } from "@/components/scripts/script-ai-draft-review-panel";
import { ScriptAiPipelinePanel } from "@/components/scripts/script-ai-pipeline-panel";
import { ScriptDocumentEditor } from "@/components/scripts/script-document-editor";
import { ScriptDocumentNavigator } from "@/components/scripts/script-document-navigator";
import { ScriptHeader } from "@/components/scripts/script-header";
import { ScriptProgressPanel } from "@/components/scripts/script-progress-panel";
import { ScriptQualityPanel } from "@/components/scripts/script-quality-panel";
import { UnsavedChangesDialog } from "@/components/scripts/unsaved-changes-dialog";
import { VersionHistoryPanel } from "@/components/scripts/version-history-panel";
import { WorkflowPanel } from "@/components/scripts/workflow-panel";
import {
  resolveWorkflowAction,
  type WorkflowActionKind,
} from "@/components/scripts/workflow-action-button";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextArea, TextInput, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { aiKeys } from "@/lib/ai/hooks";
import type { ScriptAiDocumentType } from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";
import { updateScriptDocument } from "@/lib/api/projects";
import type { ScriptDocument, ScriptDocumentType } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/auth-context";
import { useKnowledgePack } from "@/lib/knowledge-packs/hooks";
import { useProject, useProjectKnowledgePacks } from "@/lib/projects/hooks";
import { DOCUMENT_ORDER } from "@/lib/scripts/documents";
import {
  useCreateWorkflowVersion,
  useScript,
  useScriptWorkflow,
  useScriptWorkflowStatus,
  useSubmitWorkflowReview,
  useUpdateScript,
  scriptKeys,
} from "@/lib/scripts/hooks";
import { isDocumentComplete } from "@/lib/scripts/metrics";
import { qualityReviewHref } from "@/lib/scripts/quality";
import { formatRelativeTime } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";

type DraftMap = Record<string, string>;
type SavedAtMap = Record<string, string>;
type ErrorMap = Record<string, string>;

function docsToDraft(documents: ScriptDocument[]): DraftMap {
  const draft: DraftMap = {};
  for (const meta of DOCUMENT_ORDER) {
    const match = documents.find((d) => d.document_type === meta.type);
    draft[meta.type] = match?.content ?? "";
  }
  return draft;
}

function docsToSavedAt(documents: ScriptDocument[]): SavedAtMap {
  const map: SavedAtMap = {};
  for (const meta of DOCUMENT_ORDER) {
    const match = documents.find((d) => d.document_type === meta.type);
    if (match) map[meta.type] = match.updated_at;
  }
  return map;
}

function WorkspaceShell({ children }: { children: ReactNode }) {
  return <div className="min-h-full bg-background">{children}</div>;
}

export function ScriptWorkspace() {
  const params = useParams<{ projectId: string; scriptId: string }>();
  const projectId = params.projectId;
  const scriptId = params.scriptId;
  const router = useRouter();
  const { api } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const projectQuery = useProject(projectId);
  const scriptQuery = useScript(scriptId);
  const workflowQuery = useScriptWorkflowStatus(scriptId);
  const workflowDetailQuery = useScriptWorkflow(scriptId);
  const updateScript = useUpdateScript(scriptId);
  const createVersion = useCreateWorkflowVersion(scriptId);
  const submitReview = useSubmitWorkflowReview(scriptId);
  const packsQuery = useProjectKnowledgePacks(projectId, {
    page: 1,
    page_size: 50,
  });

  const [drafts, setDrafts] = useState<DraftMap>({});
  const [baseline, setBaseline] = useState<DraftMap>({});
  const [savedAt, setSavedAt] = useState<SavedAtMap>({});
  const [errors, setErrors] = useState<ErrorMap>({});
  const [activeType, setActiveType] = useState<string>(DOCUMENT_ORDER[0]!.type);
  const [saving, setSaving] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [rightDrawer, setRightDrawer] = useState<"progress" | "context" | null>(
    null,
  );
  const [justSavedAt, setJustSavedAt] = useState<number | null>(null);
  const [metaOpen, setMetaOpen] = useState(false);
  const [metaTitle, setMetaTitle] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [metaPackId, setMetaPackId] = useState<string>("");
  const [confirmVersion, setConfirmVersion] = useState(false);
  const [confirmReview, setConfirmReview] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const leaveHref = useRef<string | null>(null);
  const savingRef = useRef(false);
  const [aiDraftDocumentType, setAiDraftDocumentType] =
    useState<ScriptAiDocumentType | null>(null);
  const [aiReviewGenerationId, setAiReviewGenerationId] = useState<
    string | null
  >(null);
  const [aiReviewDocumentType, setAiReviewDocumentType] =
    useState<ScriptAiDocumentType | null>(null);
  const [qualityReviewOpen, setQualityReviewOpen] = useState(false);

  const packId = scriptQuery.data?.knowledge_pack_id ?? null;
  const packQuery = useKnowledgePack(packId ?? "");

  useEffect(() => {
    if (!scriptQuery.data || hydrated) return;
    if (scriptQuery.data.project_id !== projectId) return;
    const next = docsToDraft(scriptQuery.data.documents);
    setDrafts(next);
    setBaseline(next);
    setSavedAt(docsToSavedAt(scriptQuery.data.documents));
    setMetaTitle(scriptQuery.data.title);
    setMetaDescription(scriptQuery.data.description ?? "");
    setMetaPackId(scriptQuery.data.knowledge_pack_id ?? "");
    setHydrated(true);
  }, [scriptQuery.data, hydrated, projectId]);

  useEffect(() => {
    setHydrated(false);
    setJustSavedAt(null);
  }, [scriptId]);

  const dirtyKeys = useMemo(
    () =>
      DOCUMENT_ORDER.map((d) => d.type).filter(
        (type) => (drafts[type] ?? "") !== (baseline[type] ?? ""),
      ),
    [drafts, baseline],
  );
  const isDirty = dirtyKeys.length > 0;
  const docsComplete = useMemo(
    () =>
      DOCUMENT_ORDER.every((meta) =>
        isDocumentComplete(drafts[meta.type] ?? "", meta),
      ),
    [drafts],
  );

  const savedLabel = useMemo(() => {
    if (justSavedAt && Date.now() - justSavedAt < 60_000) return "just now";
    const values = Object.values(savedAt);
    if (values.length === 0) return null;
    const latest = values.reduce((a, b) =>
      new Date(a).getTime() > new Date(b).getTime() ? a : b,
    );
    return formatRelativeTime(latest);
  }, [justSavedAt, savedAt]);

  const workflowAction = resolveWorkflowAction(
    workflowQuery.data,
    docsComplete,
    workflowDetailQuery.data?.latest_approval,
  );
  const saveFailed = Object.keys(errors).length > 0;

  const focusDocument = useCallback((type: string) => {
    setActiveType(type);
    setDrawerOpen(false);
    const el = document.getElementById(`document-${type}`);
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (typeof window !== "undefined" && window.history?.replaceState) {
      window.history.replaceState(null, "", `#${type}`);
    }
  }, []);

  const onDocumentChange = useCallback((type: string, value: string) => {
    setDrafts((prev) => {
      if (prev[type] === value) return prev;
      return { ...prev, [type]: value };
    });
  }, []);

  async function saveDocuments(keys: string[]): Promise<boolean> {
    if (keys.length === 0 || savingRef.current) return true;
    savingRef.current = true;
    setSaving(true);
    setErrors((prev) => {
      const next = { ...prev };
      for (const key of keys) delete next[key];
      return next;
    });

    const snapshot = drafts;
    const results = await Promise.all(
      keys.map(async (documentType) => {
        try {
          const updated = await updateScriptDocument(
            api,
            scriptId,
            documentType,
            { content: snapshot[documentType] ?? "" },
          );
          return { documentType, ok: true as const, updated };
        } catch (err) {
          const detail =
            err instanceof ApiError ? err.detail : "Could not save document.";
          return { documentType, ok: false as const, detail };
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
        nextBaseline[result.documentType] = result.updated.content;
        nextSavedAt[result.documentType] = result.updated.updated_at;
      } else {
        nextErrors[result.documentType] = result.detail;
      }
    }

    setBaseline(nextBaseline);
    setSavedAt(nextSavedAt);
    setErrors((prev) => ({ ...prev, ...nextErrors }));
    setSaving(false);
    savingRef.current = false;

    void queryClient.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });

    if (successCount === keys.length) {
      setJustSavedAt(Date.now());
      toast({ title: "Script saved", tone: "success" });
      return true;
    }
    if (successCount > 0) {
      toast({
        title: "Some documents failed to save",
        description: "Local edits are preserved. Retry failed documents.",
        tone: "error",
      });
    } else {
      toast({
        title: "Save failed",
        description: "Local edits are preserved. Try again.",
        tone: "error",
      });
    }
    return false;
  }

  async function ensureSaved(): Promise<boolean> {
    if (!isDirty) return true;
    return saveDocuments(dirtyKeys);
  }

  function openAiDraft(documentType: ScriptAiDocumentType) {
    setAiDraftDocumentType(documentType);
    focusDocument(documentType);
  }

  function handleDraftReady(generationId: string) {
    const documentType = aiDraftDocumentType;
    setAiDraftDocumentType(null);
    if (!documentType) return;
    setAiReviewDocumentType(documentType);
    setAiReviewGenerationId(generationId);
  }

  function handleQualityReviewReady(generationId: string) {
    setQualityReviewOpen(false);
    void queryClient.invalidateQueries({
      queryKey: aiKeys.scriptQualityReviews(scriptId),
    });
    router.push(qualityReviewHref(projectId, scriptId, generationId));
  }

  async function handleDraftApplied({
    document,
  }: {
    document: ScriptDocument;
    generationId: string;
    staleInput: boolean;
  }) {
    const documentType = document.document_type as ScriptAiDocumentType;
    setAiReviewGenerationId(null);
    setAiReviewDocumentType(null);

    // Refresh only the applied document; preserve dirty drafts on other docs.
    setDrafts((prev) => ({ ...prev, [documentType]: document.content }));
    setBaseline((prev) => ({ ...prev, [documentType]: document.content }));
    setSavedAt((prev) => ({ ...prev, [documentType]: document.updated_at }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[documentType];
      return next;
    });

    void queryClient.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });

    toast({
      title: "AI draft applied",
      description: `${DOCUMENT_ORDER.find((d) => d.type === documentType)?.title ?? "Document"} updated. Review before creating a version.`,
      tone: "success",
    });
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const meta = event.metaKey || event.ctrlKey;
      if (meta && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void saveDocuments(dirtyKeys);
      }
      if (event.altKey && !event.metaKey && !event.ctrlKey) {
        if (event.key === "1") {
          event.preventDefault();
          focusDocument("discovery_brief");
        }
        if (event.key === "2") {
          event.preventDefault();
          focusDocument("story_spine");
        }
        if (event.key === "3") {
          event.preventDefault();
          focusDocument("master_script");
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  useEffect(() => {
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (!isDirty) return;
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (!isDirty) return;
      const target = event.target as HTMLElement | null;
      const anchor = target?.closest("a[href]") as HTMLAnchorElement | null;
      if (!anchor) return;
      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#") || href.startsWith("mailto:")) return;
      if (href.startsWith("http") && !href.includes(window.location.host)) return;
      event.preventDefault();
      leaveHref.current = href;
      setLeaveOpen(true);
    }
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [isDirty]);

  async function onWorkflowAction(kind: WorkflowActionKind) {
    if (kind === "continue_writing" || kind === "revisions_requested") {
      const incomplete = DOCUMENT_ORDER.find(
        (meta) => !isDocumentComplete(drafts[meta.type] ?? "", meta),
      );
      focusDocument(incomplete?.type ?? "discovery_brief");
      return;
    }
    if (kind === "create_version") {
      setConfirmVersion(true);
      return;
    }
    if (kind === "submit_review") {
      setConfirmReview(true);
      return;
    }
    if (kind === "view_review") {
      const approvalId = workflowQuery.data?.pending_approval?.id;
      if (approvalId) {
        router.push(`/reviews/${approvalId}`);
      } else {
        router.push("/reviews?status=pending");
      }
      return;
    }
  }

  async function runCreateVersion() {
    const saved = await ensureSaved();
    if (!saved) {
      toast({
        title: "Save required",
        description: "Fix save errors before creating a version.",
        tone: "error",
      });
      return;
    }
    try {
      const result = await createVersion.mutateAsync();
      setConfirmVersion(false);
      void workflowQuery.refetch();
      toast({
        title: `Version ${result.content_version.version_number} created`,
        tone: "success",
      });
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      toast({
        title: status === 409 ? "Version conflict" : "Could not create version",
        description:
          err instanceof ApiError
            ? err.detail
            : "Refresh and try again.",
        tone: "error",
      });
    }
  }

  async function runSubmitReview() {
    if (isDirty) {
      toast({
        title: "Save changes first",
        description: "Unsaved edits must be saved before submit for review.",
        tone: "error",
      });
      return;
    }
    try {
      await submitReview.mutateAsync();
      setConfirmReview(false);
      void workflowQuery.refetch();
      toast({ title: "Submitted for review", tone: "success" });
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      toast({
        title: status === 409 ? "Review conflict" : "Could not submit review",
        description:
          err instanceof ApiError ? err.detail : "Refresh and try again.",
        tone: "error",
      });
    }
  }

  async function saveMeta() {
    try {
      await updateScript.mutateAsync({
        title: metaTitle.trim(),
        description: metaDescription.trim() || null,
        knowledge_pack_id: metaPackId || null,
      });
      setMetaOpen(false);
      toast({ title: "Script details updated", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not update script",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  if (scriptQuery.isLoading || projectQuery.isLoading) {
    return (
      <WorkspaceShell>
        <div className="px-4 py-8 sm:px-8" data-testid="script-workspace-loading">
          <LoadingSkeleton className="mb-6 h-24" />
          <div className="grid gap-8 lg:grid-cols-[13rem_minmax(0,1fr)_16rem]">
            <LoadingSkeleton className="hidden h-96 lg:block" />
            <LoadingSkeleton className="h-[36rem]" />
            <LoadingSkeleton className="hidden h-96 xl:block" />
          </div>
        </div>
      </WorkspaceShell>
    );
  }

  if (scriptQuery.isError || !scriptQuery.data) {
    const status =
      scriptQuery.error instanceof ApiError ? scriptQuery.error.status : 0;
    if (status === 404) {
      return (
        <WorkspaceShell>
          <div className="px-4 py-16 sm:px-8">
            <EmptyState
              title="Script not found"
              description="It may have been archived or you may not have access."
              action={
                <Link
                  href={`/projects/${projectId}/scripts`}
                  className="text-sm text-brand-orange underline"
                >
                  Back to Scripts
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
              description="You do not have permission to view this script."
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
              scriptQuery.error instanceof ApiError
                ? scriptQuery.error.detail
                : "Unable to load script."
            }
            action={
              <button
                type="button"
                className="text-sm text-brand-orange underline"
                onClick={() => void scriptQuery.refetch()}
              >
                Try again
              </button>
            }
          />
        </div>
      </WorkspaceShell>
    );
  }

  if (scriptQuery.data.project_id !== projectId) {
    return (
      <WorkspaceShell>
        <div className="px-4 py-16 sm:px-8">
          <EmptyState
            title="Script not in this project"
            description="Open the script from its project Scripts list."
            action={
              <Link
                href={`/projects/${scriptQuery.data.project_id}/scripts/${scriptId}`}
                className="text-sm text-brand-orange underline"
              >
                Go to correct project
              </Link>
            }
          />
        </div>
      </WorkspaceShell>
    );
  }

  if (!hydrated) {
    return (
      <WorkspaceShell>
        <div className="px-4 py-8 sm:px-8" data-testid="script-workspace-hydrating">
          <LoadingSkeleton className="mb-6 h-24" />
          <LoadingSkeleton className="h-[36rem]" />
        </div>
      </WorkspaceShell>
    );
  }

  const script = scriptQuery.data;
  const project = projectQuery.data;
  const archived = script.status === "archived";
  const readOnly = archived;
  const hasMasterScript = (drafts.master_script ?? "").trim().length > 0;

  return (
    <WorkspaceShell>
      <ScriptHeader
        project={project}
        script={script}
        knowledgePackName={packQuery.data?.name ?? null}
        saving={saving}
        dirty={isDirty}
        savedLabel={savedLabel}
        saveFailed={saveFailed}
        workflowAction={workflowAction}
        workflowLoading={createVersion.isPending || submitReview.isPending}
        onSave={() => void saveDocuments(dirtyKeys)}
        onReviewQuality={
          readOnly || !hasMasterScript
            ? undefined
            : () => setQualityReviewOpen(true)
        }
        onCreateVersion={() => setConfirmVersion(true)}
        onWorkflowAction={(kind) => void onWorkflowAction(kind)}
        onOpenNav={() => setDrawerOpen(true)}
        onEditMeta={() => {
          setMetaTitle(script.title);
          setMetaDescription(script.description ?? "");
          setMetaPackId(script.knowledge_pack_id ?? "");
          setMetaOpen(true);
        }}
      />

      {archived ? (
        <div className="border-b border-border bg-surface px-4 py-2 text-center text-sm text-muted-foreground">
          This script is archived. Documents are read-only.
        </div>
      ) : null}

      <SectionDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Documents"
      >
        <ScriptDocumentNavigator
          contents={drafts}
          activeType={activeType}
          onNavigate={focusDocument}
        />
      </SectionDrawer>

      <div className="mx-auto grid max-w-[96rem] gap-8 px-4 py-6 sm:px-8 lg:grid-cols-[13rem_minmax(0,42rem)] lg:justify-between xl:grid-cols-[13rem_minmax(0,42rem)_17rem]">
        <aside className="hidden lg:block">
          <div className="sticky top-32 space-y-4">
            <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Documents
            </p>
            <ScriptDocumentNavigator
              contents={drafts}
              activeType={activeType}
              onNavigate={focusDocument}
            />
          </div>
        </aside>

        <div className="min-w-0">
          <div className="mb-4 flex flex-wrap gap-2 xl:hidden">
            <Button
              type="button"
              variant="secondary"
              className="h-9"
              onClick={() => setRightDrawer("progress")}
            >
              Progress & workflow
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="h-9"
              onClick={() => setRightDrawer("context")}
            >
              Knowledge Pack
            </Button>
          </div>

          <div className="divide-y divide-border/70">
            {DOCUMENT_ORDER.map((meta) => (
              <ScriptDocumentEditor
                key={meta.type}
                meta={meta}
                content={drafts[meta.type] ?? ""}
                dirty={dirtyKeys.includes(meta.type as ScriptDocumentType)}
                savedAt={savedAt[meta.type] ?? null}
                error={errors[meta.type] ?? null}
                readOnly={readOnly}
                active={activeType === meta.type}
                onChange={(value) => onDocumentChange(meta.type, value)}
                onRetry={() => void saveDocuments([meta.type])}
                onGenerateAiDraft={
                  readOnly
                    ? undefined
                    : () => openAiDraft(meta.type as ScriptAiDocumentType)
                }
              />
            ))}
          </div>
        </div>

        <div className="hidden space-y-4 xl:block">
          <div className="sticky top-32 space-y-4">
            {!readOnly ? (
              <ScriptAiPipelinePanel
                contents={drafts}
                activeType={activeType}
                onGenerate={openAiDraft}
                onFocusDocument={focusDocument}
              />
            ) : null}
            <ScriptQualityPanel
              projectId={projectId}
              scriptId={scriptId}
              hasMasterScript={hasMasterScript}
              readOnly={readOnly}
              onReview={() => setQualityReviewOpen(true)}
            />
            <ScriptProgressPanel contents={drafts} />
            <WorkflowPanel
              workflow={workflowQuery.data}
              latestApproval={workflowDetailQuery.data?.latest_approval}
              loading={workflowQuery.isLoading}
              error={
                workflowQuery.isError
                  ? workflowQuery.error instanceof ApiError
                    ? workflowQuery.error.detail
                    : "Unable to load workflow."
                  : null
              }
              onRetry={() => void workflowQuery.refetch()}
            />
            <KnowledgePackContextPanel
              projectId={projectId}
              knowledgePackId={packId}
              onAssociate={() => setMetaOpen(true)}
            />
            <VersionHistoryPanel
              projectId={projectId}
              scriptId={scriptId}
              workflow={workflowQuery.data}
              latestApproval={workflowDetailQuery.data?.latest_approval}
            />
          </div>
        </div>
      </div>

      <Modal
        open={rightDrawer !== null}
        onClose={() => setRightDrawer(null)}
        title={rightDrawer === "context" ? "Knowledge Pack" : "Progress & workflow"}
        size="lg"
      >
        <div className="space-y-4 overflow-y-auto">
          {rightDrawer === "context" ? (
            <KnowledgePackContextPanel
              projectId={projectId}
              knowledgePackId={packId}
              onAssociate={() => {
                setRightDrawer(null);
                setMetaOpen(true);
              }}
            />
          ) : (
            <>
              {!readOnly ? (
                <ScriptAiPipelinePanel
                  contents={drafts}
                  activeType={activeType}
                  onGenerate={(type) => {
                    setRightDrawer(null);
                    openAiDraft(type);
                  }}
                  onFocusDocument={(type) => {
                    setRightDrawer(null);
                    focusDocument(type);
                  }}
                />
              ) : null}
              <ScriptQualityPanel
                projectId={projectId}
                scriptId={scriptId}
                hasMasterScript={hasMasterScript}
                readOnly={readOnly}
                onReview={() => {
                  setRightDrawer(null);
                  setQualityReviewOpen(true);
                }}
              />
              <ScriptProgressPanel contents={drafts} />
              <WorkflowPanel
                workflow={workflowQuery.data}
                latestApproval={workflowDetailQuery.data?.latest_approval}
                loading={workflowQuery.isLoading}
                onRetry={() => void workflowQuery.refetch()}
              />
              <VersionHistoryPanel
                projectId={projectId}
                scriptId={scriptId}
                workflow={workflowQuery.data}
                latestApproval={workflowDetailQuery.data?.latest_approval}
              />
            </>
          )}
        </div>
      </Modal>

      <Modal
        open={metaOpen}
        onClose={() => setMetaOpen(false)}
        title="Script details"
        description="Project code and script code stay read-only."
      >
        <div className="space-y-4">
          <Field label="Project code" htmlFor="meta-project-code">
            <TextInput
              id="meta-project-code"
              value={project?.project_code ?? ""}
              readOnly
            />
          </Field>
          <Field label="Script code" htmlFor="meta-script-code">
            <TextInput
              id="meta-script-code"
              value={script.script_code}
              readOnly
            />
          </Field>
          <Field label="Title" htmlFor="meta-title">
            <TextInput
              id="meta-title"
              value={metaTitle}
              onChange={(e) => setMetaTitle(e.target.value)}
            />
          </Field>
          <Field label="Description" htmlFor="meta-description">
            <TextArea
              id="meta-description"
              value={metaDescription}
              onChange={(e) => setMetaDescription(e.target.value)}
            />
          </Field>
          <Field label="Knowledge Pack" htmlFor="meta-pack">
            <TextSelect
              id="meta-pack"
              value={metaPackId}
              onChange={(e) => setMetaPackId(e.target.value)}
            >
              <option value="">None</option>
              {(packsQuery.data?.items ?? []).map((pack) => (
                <option key={pack.id} value={pack.id}>
                  {pack.name}
                </option>
              ))}
            </TextSelect>
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setMetaOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              loading={updateScript.isPending}
              onClick={() => void saveMeta()}
            >
              Save details
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        open={confirmVersion}
        onClose={() => setConfirmVersion(false)}
        title="Create version"
        description="Snapshots the current Script Documents into an immutable Content Version and moves the workflow to versioning."
      >
        <ul className="mb-4 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Unsaved edits will be saved first.</li>
          <li>Active version will point to the new snapshot.</li>
          <li>You can submit for review after the version exists.</li>
        </ul>
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setConfirmVersion(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            loading={createVersion.isPending || saving}
            onClick={() => void runCreateVersion()}
          >
            Create Version
          </Button>
        </div>
      </Modal>

      <Modal
        open={confirmReview}
        onClose={() => setConfirmReview(false)}
        title="Submit for review"
        description="Requires an active version and a clean workspace (no unsaved changes)."
      >
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setConfirmReview(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            loading={submitReview.isPending}
            onClick={() => void runSubmitReview()}
          >
            Submit for Review
          </Button>
        </div>
      </Modal>

      <UnsavedChangesDialog
        open={leaveOpen}
        saving={saving}
        onStay={() => {
          setLeaveOpen(false);
          leaveHref.current = null;
        }}
        onDiscard={() => {
          const href = leaveHref.current;
          setLeaveOpen(false);
          leaveHref.current = null;
          setDrafts(baseline);
          setErrors({});
          if (href) router.push(href);
        }}
        onSaveAndContinue={() => {
          void (async () => {
            const ok = await saveDocuments(dirtyKeys);
            if (!ok) return;
            const href = leaveHref.current;
            setLeaveOpen(false);
            leaveHref.current = null;
            if (href) router.push(href);
          })();
        }}
      />

      {aiDraftDocumentType ? (
        <GenerateScriptAiDraftDialog
          open
          onClose={() => setAiDraftDocumentType(null)}
          scriptId={scriptId}
          documentType={aiDraftDocumentType}
          scriptTitle={script.title}
          isDirty={isDirty}
          onSaveThenGenerate={ensureSaved}
          onDraftReady={handleDraftReady}
        />
      ) : null}

      <ReviewScriptQualityDialog
        open={qualityReviewOpen}
        onClose={() => setQualityReviewOpen(false)}
        scriptId={scriptId}
        scriptTitle={script.title}
        isDirty={isDirty}
        onSaveThenReview={ensureSaved}
        onReviewReady={handleQualityReviewReady}
      />

      <Modal
        open={Boolean(aiReviewGenerationId && aiReviewDocumentType)}
        onClose={() => {
          setAiReviewGenerationId(null);
          setAiReviewDocumentType(null);
        }}
        title="Review AI Draft"
        description="Compare the generated draft with the current document, then apply when ready."
        size="lg"
      >
        {aiReviewGenerationId && aiReviewDocumentType ? (
          <ScriptAiDraftReviewPanel
            scriptId={scriptId}
            documentType={aiReviewDocumentType}
            generationId={aiReviewGenerationId}
            currentContent={drafts[aiReviewDocumentType] ?? ""}
            onApplied={(result) => void handleDraftApplied(result)}
            onClose={() => {
              setAiReviewGenerationId(null);
              setAiReviewDocumentType(null);
            }}
          />
        ) : null}
      </Modal>
    </WorkspaceShell>
  );
}
