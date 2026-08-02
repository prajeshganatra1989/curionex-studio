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
  useCreateScriptQualityReview,
  useGenerationForJob,
  usePollAiJob,
} from "@/lib/ai/hooks";
import { ApiError } from "@/lib/api/client";

type ReviewScriptQualityDialogProps = {
  open: boolean;
  onClose: () => void;
  scriptId: string;
  scriptTitle: string;
  /** True when the workspace has unsaved edits that should be saved first. */
  isDirty?: boolean;
  /** Save dirty drafts, then allow review. Return true on success. */
  onSaveThenReview?: () => Promise<boolean>;
  onReviewReady: (generationId: string) => void;
};

type Phase = "form" | "polling" | "resolving" | "failed";

export function ReviewScriptQualityDialog({
  open,
  onClose,
  scriptId,
  scriptTitle,
  isDirty = false,
  onSaveThenReview,
  onReviewReady,
}: ReviewScriptQualityDialogProps) {
  const { toast } = useToast();
  const providersQuery = useAiProviders();
  const openaiProvider = useMemo(
    () => providersQuery.data?.find((p) => p.code === "openai"),
    [providersQuery.data],
  );
  const modelsQuery = useAiModels(openaiProvider?.id);
  const models = modelsQuery.data ?? [];
  const settingsQuery = useAiSettings();

  const [modelId, setModelId] = useState("");
  const [language, setLanguage] = useState("English");
  const [targetDuration, setTargetDuration] = useState("60");
  const [targetWpm, setTargetWpm] = useState("150");
  const [phase, setPhase] = useState<Phase>("form");
  const [jobId, setJobId] = useState<string | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);
  const [savingBeforeReview, setSavingBeforeReview] = useState(false);

  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());
  const createReview = useCreateScriptQualityReview(scriptId);
  const jobQuery = usePollAiJob(jobId);
  const cancelJob = useCancelAiJob(jobId ?? "");
  const job = jobQuery.data;
  const jobStatus = job?.status;

  const generationQuery = useGenerationForJob(jobId, {
    enabled: jobStatus === "completed" && !job?.generation_id,
  });

  useEffect(() => {
    if (!open) return;
    idempotencyKeyRef.current = crypto.randomUUID();
    setPhase("form");
    setJobId(null);
    setFailureMessage(null);
    setModelId("");
    setLanguage("English");
    const duration =
      settingsQuery.data?.default_target_duration_seconds ?? 60;
    const wpm = settingsQuery.data?.default_target_words_per_minute ?? 150;
    setTargetDuration(String(duration));
    setTargetWpm(String(wpm));
    setSavingBeforeReview(false);
  }, [open, settingsQuery.data]);

  useEffect(() => {
    if (jobStatus === "failed") {
      setFailureMessage(job?.error_message ?? "Quality review failed.");
      setPhase("failed");
    } else if (jobStatus === "cancelled") {
      setFailureMessage("Quality review was cancelled.");
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
      onReviewReady(fromJob);
      return;
    }
    if (generationQuery.isLoading) return;
    if (generationQuery.data) {
      onReviewReady(generationQuery.data);
      return;
    }
    if (generationQuery.isFetched && !generationQuery.data) {
      setFailureMessage(
        "Review completed, but the generation could not be located. Check Generation History.",
      );
      setPhase("failed");
    }
  }, [
    phase,
    job?.generation_id,
    generationQuery.isLoading,
    generationQuery.isFetched,
    generationQuery.data,
    onReviewReady,
  ]);

  async function startReview() {
    if (createReview.isPending) return;
    setFailureMessage(null);
    try {
      const durationSeconds = Number.parseInt(targetDuration, 10);
      const wpm = Number.parseInt(targetWpm, 10);
      const createdJob = await createReview.mutateAsync({
        model_id: modelId || undefined,
        language: language.trim() || "English",
        target_duration_seconds:
          Number.isFinite(durationSeconds) && durationSeconds > 0
            ? durationSeconds
            : undefined,
        target_words_per_minute:
          Number.isFinite(wpm) && wpm > 0 ? wpm : undefined,
        idempotency_key: idempotencyKeyRef.current,
      });
      setJobId(createdJob.id);
      if (createdJob.generation_id && createdJob.status === "completed") {
        onReviewReady(createdJob.generation_id);
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
            createdJob.error_message ?? "Quality review did not complete.",
          );
        }
      } else {
        setPhase("polling");
      }
    } catch (error) {
      const detail =
        error instanceof ApiError
          ? error.detail
          : "Unable to start quality review.";
      toast({
        title: "Could not start review",
        description: detail,
        tone: "error",
      });
    }
  }

  async function handleSubmit() {
    if (createReview.isPending || savingBeforeReview) return;

    if (isDirty && onSaveThenReview) {
      setSavingBeforeReview(true);
      try {
        const saved = await onSaveThenReview();
        if (!saved) {
          toast({
            title: "Save required",
            description: "Fix save errors before running a quality review.",
            tone: "error",
          });
          return;
        }
      } finally {
        setSavingBeforeReview(false);
      }
    }

    await startReview();
  }

  async function handleCancel() {
    if (!jobId) return;
    try {
      await cancelJob.mutateAsync();
      toast({ title: "Quality review cancelled", tone: "info" });
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

  const submitLabel = isDirty ? "Save Before Review" : "Review Script Quality";
  const submitting = createReview.isPending || savingBeforeReview;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Review Script Quality"
      description={`Advisory AI review of the Master Script for "${scriptTitle}".`}
      size="md"
    >
      <div
        className="mb-4 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">Advisory only — AI never approves content.</p>
        <p className="mt-0.5 text-muted-foreground">
          Scores and suggestions require human judgment. Nothing is written to
          the Master Script until you explicitly apply a suggestion. Applying
          never creates a Content Version.
        </p>
      </div>

      {phase === "form" ? (
        <div className="space-y-4" data-testid="script-quality-review-form">
          {isDirty ? (
            <div
              className="rounded-lg border border-border bg-surface/60 px-3 py-2.5 text-sm text-muted-foreground"
              data-testid="script-quality-dirty-hint"
            >
              You have unsaved edits. They will be saved before the review so
              scoring uses the latest Master Script.
            </div>
          ) : null}

          <Field
            label="Model"
            htmlFor="script-quality-model"
            hint="OpenAI models only. Leave blank to use the default."
          >
            <TextSelect
              id="script-quality-model"
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

          <Field label="Language" htmlFor="script-quality-language">
            <TextInput
              id="script-quality-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="English"
              maxLength={64}
            />
          </Field>

          <Field
            label="Target duration (seconds)"
            htmlFor="script-quality-duration"
          >
            <TextInput
              id="script-quality-duration"
              type="number"
              min={15}
              max={300}
              value={targetDuration}
              onChange={(e) => setTargetDuration(e.target.value)}
            />
          </Field>

          <Field
            label="Words per minute"
            htmlFor="script-quality-wpm"
            hint="Used for pacing and duration-fit checks."
          >
            <TextInput
              id="script-quality-wpm"
              type="number"
              min={80}
              max={220}
              value={targetWpm}
              onChange={(e) => setTargetWpm(e.target.value)}
            />
          </Field>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleSubmit()}
              loading={submitting}
              disabled={submitting}
              data-testid="script-quality-review-submit"
            >
              {submitLabel}
            </Button>
          </div>
        </div>
      ) : null}

      {phase === "polling" || phase === "resolving" ? (
        <div
          className="flex flex-col items-center gap-4 py-8 text-center"
          data-testid="script-quality-review-progress"
        >
          <Loader2 className="h-6 w-6 animate-spin text-brand-orange" />
          <div>
            <p className="text-sm font-medium text-foreground">
              {phase === "resolving"
                ? "Finalizing review…"
                : "Reviewing script quality…"}
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
              Cancel review
            </Button>
          ) : null}
        </div>
      ) : null}

      {phase === "failed" ? (
        <div className="space-y-4" data-testid="script-quality-review-error">
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
