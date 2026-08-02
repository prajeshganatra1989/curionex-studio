import type { ApiClient } from "@/lib/api/client";
import type {
  CreateProjectFromTopicInput,
  CreateProjectFromTopicResponse,
  EditorialTopic,
  EditorialTopicCreateInput,
  EditorialTopicCreateResponse,
  EditorialTopicListParams,
  EditorialTopicListResponse,
  EditorialTopicSummary,
  EditorialTopicUpdateInput,
} from "@/lib/editorial/types";

function toQuery(
  params: Record<string, string | number | boolean | undefined | null>,
) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function listEditorialTopics(
  client: ApiClient,
  params: EditorialTopicListParams = {},
) {
  return client.get<EditorialTopicListResponse>(
    `/editorial-topics${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
      category: params.category,
      difficulty: params.difficulty,
      priority: params.priority,
      production_wave: params.production_wave,
      min_evergreen_score: params.min_evergreen_score,
      search: params.search,
      include_archived: params.include_archived,
      sort: params.sort,
    })}`,
  );
}

export function getEditorialTopicSummary(client: ApiClient) {
  return client.get<EditorialTopicSummary>("/editorial-topics/summary");
}

export function getEditorialTopic(client: ApiClient, topicId: string) {
  return client.get<EditorialTopic>(`/editorial-topics/${topicId}`);
}

export function createEditorialTopic(
  client: ApiClient,
  payload: EditorialTopicCreateInput,
) {
  return client.post<EditorialTopicCreateResponse>("/editorial-topics", payload);
}

export function updateEditorialTopic(
  client: ApiClient,
  topicId: string,
  payload: EditorialTopicUpdateInput,
) {
  return client.patch<EditorialTopic>(`/editorial-topics/${topicId}`, payload);
}

export function archiveEditorialTopic(client: ApiClient, topicId: string) {
  return client.delete<EditorialTopic>(`/editorial-topics/${topicId}`);
}

export function createProjectFromTopic(
  client: ApiClient,
  topicId: string,
  payload: CreateProjectFromTopicInput = {},
) {
  return client.post<CreateProjectFromTopicResponse>(
    `/editorial-topics/${topicId}/create-project`,
    payload,
  );
}
