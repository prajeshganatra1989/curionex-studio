"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, TextInput } from "@/components/ui/field";
import { useToast } from "@/components/ui/toast";
import {
  useDeleteProviderCredentials,
  useSetProviderCredentials,
  useUpdateAiProvider,
} from "@/lib/ai/hooks";
import type { AiProvider } from "@/lib/ai/types";

type ProviderCardProps = {
  provider: AiProvider;
};

export function ProviderCard({ provider }: ProviderCardProps) {
  const { toast } = useToast();
  const updateProvider = useUpdateAiProvider(provider.id);
  const setCredentials = useSetProviderCredentials(provider.id);
  const deleteCredentials = useDeleteProviderCredentials(provider.id);

  const [baseUrl, setBaseUrl] = useState(provider.base_url ?? "");
  const [apiKey, setApiKey] = useState("");

  async function handleSaveProvider() {
    try {
      await updateProvider.mutateAsync({
        base_url: baseUrl.trim() || null,
      });
      toast({ title: "Provider updated", tone: "success" });
    } catch {
      toast({ title: "Unable to update provider", tone: "error" });
    }
  }

  async function handleToggleActive() {
    try {
      await updateProvider.mutateAsync({ is_active: !provider.is_active });
      toast({ title: "Provider status updated", tone: "success" });
    } catch {
      toast({ title: "Unable to update provider", tone: "error" });
    }
  }

  async function handleSaveCredentials() {
    if (!apiKey.trim()) return;
    try {
      await setCredentials.mutateAsync({ api_key: apiKey.trim() });
      setApiKey("");
      toast({ title: "Credentials saved", tone: "success" });
    } catch {
      toast({ title: "Unable to save credentials", tone: "error" });
    }
  }

  async function handleRemoveCredentials() {
    try {
      await deleteCredentials.mutateAsync();
      toast({ title: "Credentials removed", tone: "success" });
    } catch {
      toast({ title: "Unable to remove credentials", tone: "error" });
    }
  }

  return (
    <article
      className="rounded-xl border border-border/70 bg-surface/40 p-4"
      data-testid={`provider-${provider.code}`}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            {provider.name}
          </h3>
          <p className="text-xs text-muted-foreground">{provider.code}</p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${
              provider.has_credentials
                ? "border-success/30 bg-success/15 text-success"
                : "border-border bg-muted-foreground/10 text-muted-foreground"
            }`}
          >
            {provider.has_credentials ? "Configured" : "Not configured"}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={provider.is_active}
            onChange={() => void handleToggleActive()}
            disabled={updateProvider.isPending}
          />
          Active
        </label>

        <Field label="Base URL" htmlFor={`base-url-${provider.id}`}>
          <TextInput
            id={`base-url-${provider.id}`}
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder="https://api.example.com/v1"
          />
        </Field>

        <Button
          type="button"
          variant="secondary"
          loading={updateProvider.isPending}
          onClick={() => void handleSaveProvider()}
        >
          Save provider
        </Button>

        <div className="border-t border-border pt-4">
          <Field
            label="API key"
            htmlFor={`api-key-${provider.id}`}
            hint="Keys are never displayed after saving."
          >
            <TextInput
              id={`api-key-${provider.id}`}
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Enter new API key"
              autoComplete="off"
              data-testid={`api-key-input-${provider.code}`}
            />
          </Field>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              loading={setCredentials.isPending}
              disabled={!apiKey.trim()}
              onClick={() => void handleSaveCredentials()}
            >
              Save key
            </Button>
            {provider.has_credentials ? (
              <Button
                type="button"
                variant="secondary"
                loading={deleteCredentials.isPending}
                onClick={() => void handleRemoveCredentials()}
              >
                Remove key
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  );
}
