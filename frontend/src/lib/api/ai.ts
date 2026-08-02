import type { ApiClient } from "@/lib/api/client";
import type {
  AiGeneration,
  AiGenerationListParams,
  AiJob,
  AiJobCreateInput,
  AiJobListParams,
  AiModel,
  AiModelUpdateInput,
  AiPrompt,
  AiPromptCreateInput,
  AiPromptListParams,
  AiPromptUpdateInput,
  AiPromptVersion,
  AiPromptVersionCreateInput,
  AiProvider,
  AiProviderCredentialsInput,
  AiProviderUpdateInput,
  AiSettings,
  AiSettingsUpdateInput,
  KnowledgePackAiDraftApplyInput,
  KnowledgePackAiDraftApplyResponse,
  KnowledgePackAiDraftCreateInput,
  PaginatedResponse,
} from "@/lib/ai/types";

function toQuery(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function listProviders(client: ApiClient) {
  return client.get<AiProvider[]>("/ai/providers");
}

export function getProvider(client: ApiClient, providerId: string) {
  return client.get<AiProvider>(`/ai/providers/${providerId}`);
}

export function updateProvider(
  client: ApiClient,
  providerId: string,
  payload: AiProviderUpdateInput,
) {
  return client.patch<AiProvider>(`/ai/providers/${providerId}`, payload);
}

export function setProviderCredentials(
  client: ApiClient,
  providerId: string,
  payload: AiProviderCredentialsInput,
) {
  return client.post<AiProvider>(
    `/ai/providers/${providerId}/credentials`,
    payload,
  );
}

export function deleteProviderCredentials(
  client: ApiClient,
  providerId: string,
) {
  return client.delete<void>(`/ai/providers/${providerId}/credentials`);
}

export function listModels(
  client: ApiClient,
  params: { provider_id?: string } = {},
) {
  return client.get<AiModel[]>(
    `/ai/models${toQuery({ provider_id: params.provider_id })}`,
  );
}

export function getModel(client: ApiClient, modelId: string) {
  return client.get<AiModel>(`/ai/models/${modelId}`);
}

export function updateModel(
  client: ApiClient,
  modelId: string,
  payload: AiModelUpdateInput,
) {
  return client.patch<AiModel>(`/ai/models/${modelId}`, payload);
}

export function listPrompts(
  client: ApiClient,
  params: AiPromptListParams = {},
) {
  return client.get<PaginatedResponse<AiPrompt>>(
    `/ai/prompts${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
      search: params.search,
    })}`,
  );
}

export function createPrompt(
  client: ApiClient,
  payload: AiPromptCreateInput,
) {
  return client.post<AiPrompt>("/ai/prompts", payload);
}

export function getPrompt(client: ApiClient, promptId: string) {
  return client.get<AiPrompt>(`/ai/prompts/${promptId}`);
}

export function updatePrompt(
  client: ApiClient,
  promptId: string,
  payload: AiPromptUpdateInput,
) {
  return client.patch<AiPrompt>(`/ai/prompts/${promptId}`, payload);
}

export function listPromptVersions(client: ApiClient, promptId: string) {
  return client.get<AiPromptVersion[]>(`/ai/prompts/${promptId}/versions`);
}

export function createPromptVersion(
  client: ApiClient,
  promptId: string,
  payload: AiPromptVersionCreateInput,
) {
  return client.post<AiPromptVersion>(
    `/ai/prompts/${promptId}/versions`,
    payload,
  );
}

export function activatePromptVersion(
  client: ApiClient,
  promptId: string,
  versionId: string,
) {
  return client.post<AiPrompt>(
    `/ai/prompts/${promptId}/versions/${versionId}/activate`,
  );
}

export function listJobs(client: ApiClient, params: AiJobListParams = {}) {
  return client.get<PaginatedResponse<AiJob>>(
    `/ai/jobs${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
    })}`,
  );
}

export function getJob(client: ApiClient, jobId: string) {
  return client.get<AiJob>(`/ai/jobs/${jobId}`);
}

export function createJob(client: ApiClient, payload: AiJobCreateInput) {
  return client.post<AiJob>("/ai/jobs", payload);
}

export function cancelJob(client: ApiClient, jobId: string) {
  return client.post<AiJob>(`/ai/jobs/${jobId}/cancel`);
}

export function listGenerations(
  client: ApiClient,
  params: AiGenerationListParams = {},
) {
  return client.get<PaginatedResponse<AiGeneration>>(
    `/ai/generations${toQuery({
      page: params.page,
      page_size: params.page_size,
    })}`,
  );
}

export function getGeneration(client: ApiClient, generationId: string) {
  return client.get<AiGeneration>(`/ai/generations/${generationId}`);
}

export function createKnowledgePackAiDraft(
  client: ApiClient,
  projectId: string,
  knowledgePackId: string,
  payload: KnowledgePackAiDraftCreateInput = {},
) {
  return client.post<AiJob>(
    `/projects/${projectId}/knowledge-packs/${knowledgePackId}/ai-drafts`,
    payload,
  );
}

export function applyKnowledgePackAiDraft(
  client: ApiClient,
  knowledgePackId: string,
  generationId: string,
  payload: KnowledgePackAiDraftApplyInput,
) {
  return client.post<KnowledgePackAiDraftApplyResponse>(
    `/knowledge-packs/${knowledgePackId}/ai-generations/${generationId}/apply`,
    payload,
  );
}

/**
 * Best-effort lookup of the generation produced by a job.
 *
 * The API does not expose a job -> generation link directly, but every
 * generation records its `job_id`, and generations are listed newest-first.
 * Knowledge Pack draft jobs execute synchronously, so the matching
 * generation is reliably near the top of the first page.
 */
export async function findGenerationIdForJob(
  client: ApiClient,
  jobId: string,
): Promise<string | null> {
  const response = await listGenerations(client, { page: 1, page_size: 25 });
  const match = response.items.find((item) => item.job_id === jobId);
  return match ? match.id : null;
}

export function getAiSettings(client: ApiClient) {
  return client.get<AiSettings>("/ai/settings");
}

export function updateAiSettings(
  client: ApiClient,
  payload: AiSettingsUpdateInput,
) {
  return client.put<AiSettings>("/ai/settings", payload);
}
