"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activatePromptVersion,
  cancelJob,
  createJob,
  createPrompt,
  createPromptVersion,
  deleteProviderCredentials,
  getAiSettings,
  getGeneration,
  getJob,
  getModel,
  getPrompt,
  getProvider,
  listGenerations,
  listJobs,
  listModels,
  listPrompts,
  listPromptVersions,
  listProviders,
  setProviderCredentials,
  updateAiSettings,
  updateModel,
  updatePrompt,
  updateProvider,
} from "@/lib/api/ai";
import type {
  AiGenerationListParams,
  AiJobCreateInput,
  AiJobListParams,
  AiPromptCreateInput,
  AiPromptListParams,
  AiPromptUpdateInput,
  AiPromptVersionCreateInput,
  AiProviderCredentialsInput,
  AiProviderUpdateInput,
  AiSettingsUpdateInput,
  AiModelUpdateInput,
} from "@/lib/ai/types";
import { useAuth } from "@/lib/auth/auth-context";

export const aiKeys = {
  all: ["ai"] as const,
  providers: () => [...aiKeys.all, "providers"] as const,
  provider: (id: string) => [...aiKeys.providers(), id] as const,
  models: (providerId?: string) =>
    [...aiKeys.all, "models", providerId ?? "all"] as const,
  model: (id: string) => [...aiKeys.all, "model", id] as const,
  settings: () => [...aiKeys.all, "settings"] as const,
  prompts: () => [...aiKeys.all, "prompts"] as const,
  promptList: (params: AiPromptListParams) =>
    [...aiKeys.prompts(), "list", params] as const,
  prompt: (id: string) => [...aiKeys.prompts(), "detail", id] as const,
  promptVersions: (promptId: string) =>
    [...aiKeys.prompts(), "versions", promptId] as const,
  jobs: () => [...aiKeys.all, "jobs"] as const,
  jobList: (params: AiJobListParams) =>
    [...aiKeys.jobs(), "list", params] as const,
  job: (id: string) => [...aiKeys.jobs(), "detail", id] as const,
  generations: () => [...aiKeys.all, "generations"] as const,
  generationList: (params: AiGenerationListParams) =>
    [...aiKeys.generations(), "list", params] as const,
  generation: (id: string) => [...aiKeys.generations(), "detail", id] as const,
};

export function useAiProviders() {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.providers(),
    queryFn: () => listProviders(api),
    enabled: status === "authenticated",
  });
}

export function useAiProvider(providerId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.provider(providerId ?? ""),
    queryFn: () => getProvider(api, providerId!),
    enabled: status === "authenticated" && Boolean(providerId),
  });
}

export function useUpdateAiProvider(providerId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiProviderUpdateInput) =>
      updateProvider(api, providerId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.providers() });
      void qc.invalidateQueries({ queryKey: aiKeys.provider(providerId) });
    },
  });
}

export function useSetProviderCredentials(providerId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiProviderCredentialsInput) =>
      setProviderCredentials(api, providerId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.providers() });
      void qc.invalidateQueries({ queryKey: aiKeys.provider(providerId) });
    },
  });
}

export function useDeleteProviderCredentials(providerId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteProviderCredentials(api, providerId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.providers() });
      void qc.invalidateQueries({ queryKey: aiKeys.provider(providerId) });
    },
  });
}

export function useAiModels(providerId?: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.models(providerId),
    queryFn: () => listModels(api, { provider_id: providerId }),
    enabled: status === "authenticated",
  });
}

export function useAiModel(modelId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.model(modelId ?? ""),
    queryFn: () => getModel(api, modelId!),
    enabled: status === "authenticated" && Boolean(modelId),
  });
}

export function useUpdateAiModel(modelId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiModelUpdateInput) =>
      updateModel(api, modelId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.all });
    },
  });
}

export function useAiSettings() {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.settings(),
    queryFn: () => getAiSettings(api),
    enabled: status === "authenticated",
  });
}

export function useUpdateAiSettings() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiSettingsUpdateInput) =>
      updateAiSettings(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.settings() });
    },
  });
}

export function useAiPrompts(params: AiPromptListParams = {}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.promptList(params),
    queryFn: () => listPrompts(api, params),
    enabled: status === "authenticated",
  });
}

export function useAiPrompt(promptId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.prompt(promptId ?? ""),
    queryFn: () => getPrompt(api, promptId!),
    enabled: status === "authenticated" && Boolean(promptId),
  });
}

export function useCreateAiPrompt() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiPromptCreateInput) => createPrompt(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.prompts() });
    },
  });
}

export function useUpdateAiPrompt(promptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiPromptUpdateInput) =>
      updatePrompt(api, promptId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.prompt(promptId) });
      void qc.invalidateQueries({ queryKey: aiKeys.prompts() });
    },
  });
}

export function useAiPromptVersions(promptId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.promptVersions(promptId ?? ""),
    queryFn: () => listPromptVersions(api, promptId!),
    enabled: status === "authenticated" && Boolean(promptId),
  });
}

export function useCreateAiPromptVersion(promptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiPromptVersionCreateInput) =>
      createPromptVersion(api, promptId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.prompt(promptId) });
      void qc.invalidateQueries({ queryKey: aiKeys.promptVersions(promptId) });
    },
  });
}

export function useActivateAiPromptVersion(promptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (versionId: string) =>
      activatePromptVersion(api, promptId, versionId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.prompt(promptId) });
      void qc.invalidateQueries({ queryKey: aiKeys.promptVersions(promptId) });
    },
  });
}

export function useAiJobs(params: AiJobListParams = {}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.jobList(params),
    queryFn: () => listJobs(api, params),
    enabled: status === "authenticated",
  });
}

export function useAiJob(jobId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.job(jobId ?? ""),
    queryFn: () => getJob(api, jobId!),
    enabled: status === "authenticated" && Boolean(jobId),
  });
}

export function useCreateAiJob() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiJobCreateInput) => createJob(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.jobs() });
    },
  });
}

export function useCancelAiJob(jobId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => cancelJob(api, jobId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: aiKeys.jobs() });
      void qc.invalidateQueries({ queryKey: aiKeys.job(jobId) });
    },
  });
}

export function useAiGenerations(params: AiGenerationListParams = {}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.generationList(params),
    queryFn: () => listGenerations(api, params),
    enabled: status === "authenticated",
  });
}

export function useAiGeneration(generationId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: aiKeys.generation(generationId ?? ""),
    queryFn: () => getGeneration(api, generationId!),
    enabled: status === "authenticated" && Boolean(generationId),
  });
}
