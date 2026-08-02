"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { VariableChips } from "@/components/ai/variable-chips";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextArea, TextInput, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { SectionPanel } from "@/components/ui/section-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast";
import {
  useActivateAiPromptVersion,
  useAiPrompt,
  useAiPromptVersions,
  useCreateAiPromptVersion,
  useUpdateAiPrompt,
} from "@/lib/ai/hooks";
import type { AiPromptVersion } from "@/lib/ai/types";
import { validatePromptVariables } from "@/lib/ai/variables";
import { ApiError } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";

type PromptEditorPageProps = {
  promptId: string;
};

export function PromptEditorPage({ promptId }: PromptEditorPageProps) {
  const { toast } = useToast();
  const promptQuery = useAiPrompt(promptId);
  const versionsQuery = useAiPromptVersions(promptId);
  const updatePrompt = useUpdateAiPrompt(promptId);
  const createVersion = useCreateAiPromptVersion(promptId);
  const activateVersion = useActivateAiPromptVersion(promptId);

  const prompt = promptQuery.data;
  const versions = useMemo(
    () => versionsQuery.data ?? [],
    [versionsQuery.data],
  );

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(
    null,
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState("");
  const [status, setStatus] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userTemplate, setUserTemplate] = useState("");
  const [variables, setVariables] = useState<string[]>([]);

  const activeVersionId = prompt?.active_version_id ?? null;

  const selectedVersion: AiPromptVersion | null = useMemo(() => {
    if (selectedVersionId) {
      return versions.find((v) => v.id === selectedVersionId) ?? null;
    }
    if (prompt?.active_version) return prompt.active_version;
    return versions[0] ?? null;
  }, [selectedVersionId, versions, prompt?.active_version]);

  useEffect(() => {
    if (!prompt) return;
    setName(prompt.name);
    setDescription(prompt.description ?? "");
    setPurpose(prompt.purpose ?? "");
    setStatus(prompt.status);
  }, [prompt]);

  useEffect(() => {
    if (!selectedVersion) return;
    setSystemPrompt(selectedVersion.system_prompt);
    setUserTemplate(selectedVersion.user_template);
    setVariables(selectedVersion.variables);
  }, [selectedVersion]);

  const validation = validatePromptVariables(
    systemPrompt,
    userTemplate,
    variables,
  );

  const isDirty =
    selectedVersion &&
    (systemPrompt !== selectedVersion.system_prompt ||
      userTemplate !== selectedVersion.user_template ||
      JSON.stringify(variables) !==
        JSON.stringify(selectedVersion.variables));

  const restricted =
    (promptQuery.isError &&
      promptQuery.error instanceof ApiError &&
      promptQuery.error.status === 403) ||
    (versionsQuery.isError &&
      versionsQuery.error instanceof ApiError &&
      versionsQuery.error.status === 403);

  const isLoading = promptQuery.isLoading || versionsQuery.isLoading;

  async function handleSaveMetadata() {
    try {
      await updatePrompt.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
        purpose: purpose.trim() || null,
        status: status || undefined,
      });
      toast({ title: "Prompt updated", tone: "success" });
    } catch {
      toast({ title: "Unable to update prompt", tone: "error" });
    }
  }

  async function handleSaveVersion() {
    if (!validation.valid) return;
    try {
      const version = await createVersion.mutateAsync({
        system_prompt: systemPrompt,
        user_template: userTemplate,
        variables,
      });
      setSelectedVersionId(version.id);
      toast({ title: "New version saved", tone: "success" });
    } catch {
      toast({ title: "Unable to save version", tone: "error" });
    }
  }

  async function handleActivate(versionId: string) {
    try {
      await activateVersion.mutateAsync(versionId);
      toast({ title: "Version activated", tone: "success" });
    } catch {
      toast({ title: "Unable to activate version", tone: "error" });
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title={prompt?.name ?? "Prompt editor"}
        description="Edit metadata, templates, and manage version history."
        actions={
          <Link
            href="/ai/prompts"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
          >
            Back to library
          </Link>
        }
      />

      {isLoading ? (
        <div className="space-y-4" aria-busy="true">
          <LoadingSkeleton className="h-24" />
          <LoadingSkeleton className="h-64" />
        </div>
      ) : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You do not have permission to edit prompts."
        />
      ) : null}

      {!isLoading && promptQuery.isError && !restricted ? (
        <ErrorState
          message={
            promptQuery.error instanceof ApiError
              ? promptQuery.error.detail
              : "Unable to load prompt."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => void promptQuery.refetch()}
            >
              Try again
            </button>
          }
        />
      ) : null}

      {!isLoading && prompt && !restricted ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="space-y-6">
            <SectionPanel title="Metadata">
              <div className="space-y-4 p-2">
                <Field label="Name" htmlFor="edit-name">
                  <TextInput
                    id="edit-name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                  />
                </Field>
                <Field label="Description" htmlFor="edit-description">
                  <TextInput
                    id="edit-description"
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                  />
                </Field>
                <Field label="Purpose" htmlFor="edit-purpose">
                  <TextInput
                    id="edit-purpose"
                    value={purpose}
                    onChange={(event) => setPurpose(event.target.value)}
                  />
                </Field>
                <Field label="Status" htmlFor="edit-status">
                  <TextSelect
                    id="edit-status"
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </TextSelect>
                </Field>
                <Button
                  type="button"
                  variant="secondary"
                  loading={updatePrompt.isPending}
                  onClick={() => void handleSaveMetadata()}
                >
                  Save metadata
                </Button>
              </div>
            </SectionPanel>

            <SectionPanel
              title="Templates"
              description={
                selectedVersion
                  ? `Editing v${selectedVersion.version_number}${
                      selectedVersion.id === activeVersionId ? " (active)" : ""
                    }`
                  : undefined
              }
            >
              <div className="space-y-4 p-2" data-testid="prompt-editor">
                <Field label="System prompt" htmlFor="edit-system">
                  <TextArea
                    id="edit-system"
                    value={systemPrompt}
                    onChange={(event) => setSystemPrompt(event.target.value)}
                    className="min-h-32 font-mono text-xs"
                  />
                </Field>
                <Field label="User template" htmlFor="edit-user">
                  <TextArea
                    id="edit-user"
                    value={userTemplate}
                    onChange={(event) => setUserTemplate(event.target.value)}
                    className="min-h-32 font-mono text-xs"
                  />
                </Field>
                <Field label="Variables" htmlFor="edit-variables">
                  <VariableChips
                    variables={variables}
                    onChange={setVariables}
                    errors={validation.valid ? undefined : validation.errors}
                  />
                </Field>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    loading={createVersion.isPending}
                    disabled={!validation.valid || !isDirty}
                    onClick={() => void handleSaveVersion()}
                  >
                    Save as new version
                  </Button>
                  {selectedVersion &&
                  selectedVersion.id !== activeVersionId ? (
                    <Button
                      type="button"
                      variant="secondary"
                      loading={activateVersion.isPending}
                      onClick={() => void handleActivate(selectedVersion.id)}
                    >
                      Activate version
                    </Button>
                  ) : null}
                </div>
              </div>
            </SectionPanel>
          </div>

          <SectionPanel title="Version history">
            <ul
              className="divide-y divide-border"
              data-testid="version-history"
            >
              {versions.length === 0 ? (
                <li className="px-3 py-4 text-xs text-muted-foreground">
                  No versions yet.
                </li>
              ) : (
                versions.map((version) => {
                  const isActive = version.id === activeVersionId;
                  const isSelected = selectedVersion?.id === version.id;
                  return (
                    <li key={version.id}>
                      <button
                        type="button"
                        className={`flex w-full flex-col gap-1 px-3 py-3 text-left transition hover:bg-surface-hover ${
                          isSelected ? "bg-surface-hover" : ""
                        }`}
                        onClick={() => setSelectedVersionId(version.id)}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-medium text-foreground">
                            v{version.version_number}
                          </span>
                          {isActive ? (
                            <StatusBadge status="active" />
                          ) : (
                            <StatusBadge status={version.status} />
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(version.created_at)}
                        </span>
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          </SectionPanel>
        </div>
      ) : null}
    </PageContainer>
  );
}
