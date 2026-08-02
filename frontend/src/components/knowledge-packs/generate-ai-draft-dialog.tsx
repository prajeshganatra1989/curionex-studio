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
  useCancelAiJob,
  useCreateKnowledgePackAiDraft,
  useGenerationForJob,
  usePollAiJob,
} from "@/lib/ai/hooks";
import { ApiError } from "@/lib/api/client";

const DEPTH_OPTIONS: { value: string; label: string }[] = [
  { value: "quick", label: "Quick — a light pass" },
  { value: "standard", label: "Standard" },
  { value: "deep", label: "Deep — more detail" },
];

type GenerateAiDraftDialogProps = {
  open: boolean;
  onClose: () => void;
  projectId: string;
  knowledgePackId: string;
  packName: string;
  projectName?: string;
  /** Called once a completed job's generation has been located. */
  onDraftReady: (generationId: string) => void;
};

type Phase = "form" | "polling" | "resolving" | "failed";

export function GenerateAiDraftDialog({
  open,
  onClose,
  projectId,
  knowledgePackId,
  packName,
  projectName,
  onDraftReady,
}: GenerateAiDraftDialogProps) {
  const { toast } = useToast();
  const providersQuery = useAiProviders();
  const openaiProvider = useMemo(
    () => providersQuery.data?.find((p) => p.code === "openai"),
    [providersQuery.data],
  );
  const modelsQuery = useAiModels(openaiProvider?.id);
  const models = modelsQuery.data ?? [];

  const [modelId, setModelId] = useState<string>("");
  const [targetAudience, setTargetAudience] = useState("general learners");
  const [language, setLanguage] = useState("en");
  const [desiredDepth, setDesiredDepth] = useState("standard");
  const [phase, setPhase] = useState<Phase>("form");
  const [jobId, setJobId] = useState<string | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

  const createDraft = useCreateKnowledgePackAiDraft(projectId, knowledgePackId);
  const jobQuery = usePollAiJob(jobId);
  const cancelJob = useCancelAiJob(jobId ?? "");
  const job = jobQuery.data;
  const jobStatus = job?.status;

  const generationQuery = useGenerationForJob(jobId, {
    enabled: jobStatus === "completed",
  });

  useEffect(() => {
    if (!open) return;
    idempotencyKeyRef.current = crypto.randomUUID();
    setPhase("form");
    setJobId(null);
    setFailureMessage(null);
    setModelId("");
    setTargetAudience("general learners");
    setLanguage("en");
    setDesiredDepth("standard");
  }, [open]);

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
    generationQuery.isLoading,
    generationQuery.isFetched,
    generationQuery.data,
    onDraftReady,
  ]);

  async function handleSubmit() {
    if (createDraft.isPending) return;
    setFailureMessage(null);
    try {
      const createdJob = await createDraft.mutateAsync({
        model_id: modelId || undefined,
        target_audience: targetAudience.trim() || "general learners",
        language: language.trim() || "en",
        desired_depth: desiredDepth,
        idempotency_key: idempotencyKeyRef.current,
      });
      setJobId(createdJob.id);
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
      const detail =
        error instanceof ApiError ? error.detail : "Unable to start draft generation.";
      toast({ title: "Could not generate draft", description: detail, tone: "error" });
    }
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

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Generate AI Draft"
      description={`Draft research for "${packName}"${projectName ? ` · ${projectName}` : ""}.`}
      size="md"
    >
      <div
        className="mb-4 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-sm text-foreground"
        role="note"
      >
        <p className="font-medium">AI-generated content is unverified.</p>
        <p className="mt-0.5 text-muted-foreground">
          Facts, sources, and claims require human review before publishing. Nothing
          is written to the Knowledge Pack until you review and apply it.
        </p>
      </div>

      {phase === "form" ? (
        <div className="space-y-4" data-testid="ai-draft-form">
          <Field label="Model" htmlFor="ai-draft-model" hint="OpenAI models only. Leave blank to use the default.">
            <TextSelect
              id="ai-draft-model"
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

          <Field label="Target audience" htmlFor="ai-draft-audience">
            <TextInput
              id="ai-draft-audience"
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="general learners"
              maxLength={200}
            />
          </Field>

          <Field label="Language" htmlFor="ai-draft-language">
            <TextInput
              id="ai-draft-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="en"
              maxLength={32}
            />
          </Field>

          <Field label="Desired depth" htmlFor="ai-draft-depth">
            <TextSelect
              id="ai-draft-depth"
              value={desiredDepth}
              onChange={(e) => setDesiredDepth(e.target.value)}
            >
              {DEPTH_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </TextSelect>
          </Field>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleSubmit()}
              loading={createDraft.isPending}
              disabled={createDraft.isPending}
              data-testid="ai-draft-submit"
            >
              Generate Draft
            </Button>
          </div>
        </div>
      ) : null}

      {phase === "polling" || phase === "resolving" ? (
        <div
          className="flex flex-col items-center gap-4 py-8 text-center"
          data-testid="ai-draft-progress"
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
        <div className="space-y-4" data-testid="ai-draft-error">
          <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm text-danger" role="alert">
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
