"use client";

import Link from "next/link";

import { ProviderCard } from "@/components/ai/provider-card";
import { PageContainer, PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Field, TextInput, TextSelect } from "@/components/ui/field";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { SectionPanel } from "@/components/ui/section-panel";
import { useToast } from "@/components/ui/toast";
import {
  useAiModels,
  useAiProviders,
  useAiSettings,
  useUpdateAiModel,
  useUpdateAiSettings,
} from "@/lib/ai/hooks";
import { ApiError } from "@/lib/api/client";

function SettingsSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true">
      <LoadingSkeleton className="h-40" />
      <LoadingSkeleton className="h-52" />
    </div>
  );
}

export function AiSettingsPage() {
  const { toast } = useToast();
  const providers = useAiProviders();
  const models = useAiModels();
  const settings = useAiSettings();
  const updateSettings = useUpdateAiSettings();

  const restricted =
    (providers.isError &&
      providers.error instanceof ApiError &&
      providers.error.status === 403) ||
    (settings.isError &&
      settings.error instanceof ApiError &&
      settings.error.status === 403);

  const isLoading =
    providers.isLoading || models.isLoading || settings.isLoading;
  const isError =
    !restricted &&
    (providers.isError || models.isError || settings.isError);
  const error =
    providers.error ?? models.error ?? settings.error ?? undefined;

  const modelItems = models.data ?? [];
  const settingsData = settings.data;

  async function handleSaveDefaults(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await updateSettings.mutateAsync({
        default_model_id: String(form.get("default_model_id") || "") || null,
        default_temperature: Number(form.get("default_temperature") || 0.7),
        default_max_tokens: Number(form.get("default_max_tokens") || 4096),
      });
      toast({ title: "Defaults saved", tone: "success" });
    } catch {
      toast({ title: "Unable to save defaults", tone: "error" });
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="AI Settings"
        description="Configure providers, credentials, models, and studio defaults."
        actions={
          <Link
            href="/ai"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-surface-elevated px-4 text-sm text-foreground hover:bg-surface-hover"
          >
            Back to hub
          </Link>
        }
      />

      {isLoading ? <SettingsSkeleton /> : null}

      {restricted ? (
        <EmptyState
          title="Access restricted"
          description="You need ai.manage permission to configure AI settings."
        />
      ) : null}

      {!isLoading && isError ? (
        <ErrorState
          message={
            error instanceof ApiError ? error.detail : "Unable to load settings."
          }
          action={
            <button
              type="button"
              className="text-sm text-brand-orange underline"
              onClick={() => {
                void providers.refetch();
                void models.refetch();
                void settings.refetch();
              }}
            >
              Try again
            </button>
          }
        />
      ) : null}

      {!isLoading && !isError && !restricted ? (
        <div className="space-y-6">
          <SectionPanel
            title="Studio defaults"
            description="Default model and generation parameters."
          >
            <form className="space-y-4 p-2" onSubmit={(e) => void handleSaveDefaults(e)}>
              <Field label="Default model" htmlFor="default_model_id">
                <TextSelect
                  id="default_model_id"
                  name="default_model_id"
                  defaultValue={settingsData?.default_model_id ?? ""}
                >
                  <option value="">None</option>
                  {modelItems.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.code})
                    </option>
                  ))}
                </TextSelect>
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Temperature" htmlFor="default_temperature">
                  <TextInput
                    id="default_temperature"
                    name="default_temperature"
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    defaultValue={settingsData?.default_temperature ?? 0.7}
                  />
                </Field>
                <Field label="Max tokens" htmlFor="default_max_tokens">
                  <TextInput
                    id="default_max_tokens"
                    name="default_max_tokens"
                    type="number"
                    min="1"
                    defaultValue={settingsData?.default_max_tokens ?? 4096}
                  />
                </Field>
              </div>
              <Button type="submit" loading={updateSettings.isPending}>
                Save defaults
              </Button>
            </form>
          </SectionPanel>

          <SectionPanel
            title="Providers"
            description="Enable providers and manage API credentials."
          >
            <div className="grid gap-4 p-2 lg:grid-cols-2">
              {(providers.data ?? []).map((provider) => (
                <ProviderCard key={provider.id} provider={provider} />
              ))}
            </div>
            {(providers.data ?? []).length === 0 ? (
              <EmptyState
                title="No providers"
                description="Providers will appear once configured on the backend."
              />
            ) : null}
          </SectionPanel>

          <SectionPanel
            title="Models"
            description="Toggle model availability and set the default model."
          >
            <ul
              className="divide-y divide-border rounded-lg border border-border/70"
              data-testid="models-list"
            >
              {modelItems.map((model) => (
                <ModelRow key={model.id} model={model} />
              ))}
            </ul>
            {modelItems.length === 0 ? (
              <EmptyState title="No models" description="No models registered yet." />
            ) : null}
          </SectionPanel>
        </div>
      ) : null}
    </PageContainer>
  );
}

function ModelRow({ model }: { model: import("@/lib/ai/types").AiModel }) {
  const { toast } = useToast();
  const updateModel = useUpdateAiModel(model.id);

  async function toggle(field: "is_active" | "is_default") {
    try {
      await updateModel.mutateAsync({
        [field]: !model[field],
      });
      toast({ title: "Model updated", tone: "success" });
    } catch {
      toast({ title: "Unable to update model", tone: "error" });
    }
  }

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
      <div>
        <p className="text-sm font-medium text-foreground">{model.name}</p>
        <p className="text-xs text-muted-foreground">{model.code}</p>
      </div>
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={model.is_active}
            onChange={() => void toggle("is_active")}
            disabled={updateModel.isPending}
          />
          Active
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={model.is_default}
            onChange={() => void toggle("is_default")}
            disabled={updateModel.isPending}
          />
          Default
        </label>
      </div>
    </li>
  );
}
