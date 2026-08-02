"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, TextInput, TextSelect } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import {
  useAiModels,
  useAiProviders,
  useAiSettings,
  useCancelAiJob,
  useCreateScriptAiDraft,
  useGenerationForJob,
  usePollAiJob,
  useScriptAiPrerequisites,
} from "@/lib/ai/hooks";
import type { ScriptAiDocumentType } from "@/lib/ai/types";
import { ApiError } from "@/lib/api/client";
import { DOCUMENT_BY_TYPE } from "@/lib/scripts/documents";
import { prerequisiteLabels } from "@/lib/scripts/draft";

type GenerateScriptAiDraftDialogProps = {
  open: boolean;
  onClose: () => void;
  scriptId: string;
  documentType: ScriptAiDocumentType;
  scriptTitle: string;
  /** True when the workspace has unsaved edits that should be saved first. */
  isDirty?: boolean;
  /** Save dirty drafts, then allow generation. Return true on success. */
  onSaveThenGenerate?: () => Promise<boolean>;
  onDraftReady: (generationId: string) => void;
};

type Phase = "form" | "polling" | "resolving" | "failed";

export function GenerateScriptAiDraftDialog({
  open,
  onClose,
  scriptId,
  documentType,
  scriptTitle,
  isDirty = false,
  onSaveThenGenerate,
  onDraftReady,
}: GenerateScriptAiDraftDialogProps) {
  const { toast } = useToast();
  const meta = DOCUMENT_BY_TYPE[documentType];
  const providersQuery = useAiProviders();
  const openaiProvider = useMemo(
    () => providersQuery.data?.find((p) => p.code === "openai"),
    [providersQuery.data],
  );
  const modelsQuery = useAiModels(openaiProvider?.id);
  const models = modelsQuery.data ?? [];
  const settingsQuery = useAiSettings();
  const prerequisitesQuery = useScriptAiPrerequisites(scriptId, documentType, {
    enabled: open,
  });

  const [modelId, setModelId] = useState("");
  const [language, setLanguage] = useState("English");
  const [tone, setTone] = useState("curious, cinematic, clear");
  const [targetDuration, setTargetDuration] = useState("60");
  const [targetWpm, setTargetWpm] = useState("150");
  const [phase, setPhase] = useState<Phase>("form");
  const [jobId, setJobId] = useState<string | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);
  const [savingBeforeGenerate, setSavingBeforeGenerate] = useState(false);

  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());
  const createDraft = useCreateScriptAiDraft(scriptId, documentType);
  const jobQuery = usePollAiJob(jobId);
  const cancelJob = useCancelAiJob(jobId ?? "");
  const job = jobQuery.data;
  const jobStatus = job?.status;

  const generationQuery = useGenerationForJob(jobId, {
    enabled: jobStatus === "completed" && !job?.generation_id,
  });

  const missing = prerequisitesQuery.data?.missing ?? [];
  const ready = prerequisitesQuery.data?.ready ?? missing.length === 0;
  const isMaster = documentType === "master_script";

  useEffect(() => {
    if (!open) return;
    idempotencyKeyRef.current = crypto.randomUUID();
    setPhase("form");
    setJobId(null);
    setFailureMessage(null);
    setModelId("");
    setLanguage("English");
    setTone("curious, cinematic, clear");
    const duration =
      settingsQuery.data?.default_target_duration_seconds ?? 60;
    const wpm =
      settingsQuery.data?.default_target_words_per_minute ?? 150;
    setTargetDuration(String(duration));
    setTargetWpm(String(wpm));
    setSavingBeforeGenerate(false);
  }, [open, settingsQuery.data]);

  useEffect(() => {
    if (jobStatus === "failed") {
      setFailureMessage(job?.error_message ?? "Draft generation failed.");
      setPhase("failed");
    } else if (jobStatus === "cancelled") {
      setFailureMessage("Draft generation was cancelled.");
      setPhase("failed");
    } else if (jobStatus === "completed") {
      setPhase("resolving");
    } else if (jobStatus === "queued" || jobStatus === "running") {
      setPhase("polling");
    }
  }, [jobStatus, job?.error_message]);

  useEffect(() => {
    if (phase !== "resolving") return;
    const fromJob = job?.generation_id;
    if (fromJob) {
      onDraftReady(fromJob);
      return;
    }
    if (generationQuery.isLoading) return;
    if (generationQuery.data) {
      onDraftReady(generationQuery.data);
      return;
    }
    if (generationQuery.isFetched && !generationQuery.data) {
      setFailureMessage(
        "Draft completed, but the generation could not be located. Check Generation History.",
      );
      setPhase("failed");
    }
  }, [
    phase,
    job?.generation_id,
    generationQuery.isLoading,
    generationQuery.isFetched,
    generationQuery.data,
    onDraftReady,
  ]);

  async function startGeneration() {
    if (createDraft.isPending) return;
    setFailureMessage(null);
    try {
      const durationSeconds = Number.parseInt(targetDuration, 10);
      const wpm = Number.parseInt(targetWpm, 10);
      const createdJob = await createDraft.mutateAsync({
        model_id: modelId || undefined,
        language: language.trim() || "English",
        tone: tone.trim() || "curious, cinematic, clear",
        target_duration_seconds:
          Number.isFinite(durationSeconds) && durationSeconds > 0
            ? durationSeconds
            : undefined,
        target_words_per_minute:
          isMaster && Number.isFinite(wpm) && wpm > 0 ? wpm : undefined,
        idempotency_key: idempotencyKeyRef.current,
      });
      setJobId(createdJob.id);
      if (createdJob.generation_id && createdJob.status === "completed") {
        onDraftReady(createdJob.generation_id);
        return;
      }
      if (
        createdJob.status === "completed" ||
        createdJob.status === "failed" ||
        createdJob.status === "cancelled"
      ) {
        setPhase(createdJob.status === "completed" ? "resolving" : "failed");
        if (createdJob.status !== "completed") {
          setFailureMessage(
            createdJob.error_message ?? "Draft generation did not complete.",
          );
        }
      } else {
        setPhase("polling");
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) {
        const data = error.data as { missing?: string[] } | undefined;
        if (data?.missing?.length) {
          setFailureMessage(
            `Missing prerequisites: ${prerequisiteLabels(data.missing).join(", ")}.`,
          );
          setPhase("failed");
          return;
        }
      }
      const detail =
        error instanceof ApiError
          ? error.detail
          : "Unable to start draft generation.";
      toast({
        title: "Could not generate draft",
        description: detail,
        tone: "error",
      });
    }
  }

  async function handleSubmit() {
    if (createDraft.isPending || savingBeforeGenerate) return;
    if (!ready) return;

    if (isDirty && onSaveThenGenerate) {
      setSavingBeforeGenerate(true);
      try {
        const saved = await onSaveThenGenerate();
        if (!saved) {
          toast({
            title: "Save required",
            description: "Fix save errors before generating a draft.",
            tone: "error",
          });
          return;
        }
      } finally {
        setSavingBeforeGenerate(false);
      }
    }

    await startGeneration();
  }

  async function handleCancel() {
    if (!jobId) return;
    try {
      await cancelJob.mutateAsync();
      toast({ title: "Draft generation cancelled", tone: "info" });
    } catch {
      toast({ title: "Unable to cancel job", tone: "error" });
    }
  }

  function handleRetryAfterFailure() {
    idempotencyKeyRef.current = crypto.randomUUID();
    setJobId(null);
    setFailureMessage(null);
    setPhase("form");
  }

  const submitLabel = isDirty ? "Save and Generate" : "Generate Draft";
  const submitting = createDraft.isPending || savingBeforeGenerate;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Generate AI Draft — ${meta.title}`}
      description={`Draft ${meta.title.toLowerCase()} for "${scriptTitle}".`}
      size="md"
    >
      <div
        className="mb-4 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">AI-generated content is unverified.</p>
        <p className="mt-0.5 text-muted-foreground">
          Facts, claims, and narrative details require human review. Nothing is
          written to this document until you review and apply it. Applying never
          creates a Content Version automatically.
        </p>
      </div>

      {phase === "form" ? (
        <div className="space-y-4" data-testid="script-ai-draft-form">
          {!ready ? (
            <div
              className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
              role="alert"
              data-testid="script-ai-prerequisites"
            >
              <p className="font-medium">Prerequisites missing</p>
              <p className="mt-1 text-xs">
                Complete and save{" "}
                {prerequisiteLabels(missing).join(" and ")} before generating
                this draft.
              </p>
            </div>
          ) : null}

          {isDirty ? (
            <div
              className="rounded-lg border border-border bg-surface/60 px-3 py-2.5 text-sm text-muted-foreground"
              data-testid="script-ai-dirty-hint"
            >
              You have unsaved edits. They will be saved before generation so
              the draft uses the latest document content.
            </div>
          ) : null}

          <Field
            label="Model"
            htmlFor="script-ai-draft-model"
            hint="OpenAI models only. Leave blank to use the default."
          >
            <TextSelect
              id="script-ai-draft-model"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              disabled={modelsQuery.isLoading}
            >
              <option value="">Use default OpenAI model</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </TextSelect>
          </Field>

          <Field label="Language" htmlFor="script-ai-draft-language">
            <TextInput
              id="script-ai-draft-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="English"
              maxLength={64}
            />
          </Field>

          <Field label="Tone" htmlFor="script-ai-draft-tone">
            <TextInput
              id="script-ai-draft-tone"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              placeholder="curious, cinematic, clear"
              maxLength={200}
            />
          </Field>

          <Field
            label="Target duration (seconds)"
            htmlFor="script-ai-draft-duration"
          >
            <TextInput
              id="script-ai-draft-duration"
              type="number"
              min={15}
              max={300}
              value={targetDuration}
              onChange={(e) => setTargetDuration(e.target.value)}
            />
          </Field>

          {isMaster ? (
            <Field
              label="Words per minute"
              htmlFor="script-ai-draft-wpm"
              hint="Used to size narration length for the target duration."
            >
              <TextInput
                id="script-ai-draft-wpm"
                type="number"
                min={80}
                max={220}
                value={targetWpm}
                onChange={(e) => setTargetWpm(e.target.value)}
              />
            </Field>
          ) : null}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleSubmit()}
              loading={submitting}
              disabled={submitting || !ready}
              data-testid="script-ai-draft-submit"
            >
              {submitLabel}
            </Button>
          </div>
        </div>
      ) : null}

      {phase === "polling" || phase === "resolving" ? (
        <div
          className="flex flex-col items-center gap-4 py-8 text-center"
          data-testid="script-ai-draft-progress"
        >
          <Loader2 className="h-6 w-6 animate-spin text-brand-orange" />
          <div>
            <p className="text-sm font-medium text-foreground">
              {phase === "resolving" ? "Finalizing draft…" : "Generating draft…"}
            </p>
            {job ? (
              <p className="mt-1 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <StatusBadge status={job.status} />
              </p>
            ) : null}
          </div>
          {phase === "polling" && jobStatus !== "completed" ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => void handleCancel()}
              loading={cancelJob.isPending}
            >
              Cancel generation
            </Button>
          ) : null}
        </div>
      ) : null}

      {phase === "failed" ? (
        <div className="space-y-4" data-testid="script-ai-draft-error">
          <div
            className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger"
            role="alert"
          >
            {failureMessage}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Close
            </Button>
            <Button type="button" onClick={handleRetryAfterFailure}>
              Try again
            </Button>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}
