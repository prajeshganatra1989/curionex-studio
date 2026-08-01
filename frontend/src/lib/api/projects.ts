import { ApiError, type ApiClient } from "@/lib/api/client";
import type {
  Category,
  CategoryCreateInput,
  ContentVersionSummary,
  KnowledgePackCreateInput,
  KnowledgePackDetail,
  KnowledgePackListResponse,
  KnowledgePackSection,
  KnowledgePackSectionUpdateInput,
  Project,
  ProjectCreateInput,
  ProjectListParams,
  ProjectListResponse,
  ProjectUpdateInput,
  ScriptCreateInput,
  ScriptListResponse,
  ScriptSummary,
  Tag,
  TagCreateInput,
  WorkflowStatus,
} from "@/lib/api/types";

function toQuery(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function listProjects(client: ApiClient, params: ProjectListParams = {}) {
  return client.get<ProjectListResponse>(
    `/projects${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
      category_id: params.category_id,
      tag_id: params.tag_id,
      created_by: params.created_by,
      search: params.search,
    })}`,
  );
}

export function getProject(client: ApiClient, projectId: string) {
  return client.get<Project>(`/projects/${projectId}`);
}

export function createProject(client: ApiClient, payload: ProjectCreateInput) {
  return client.post<Project>("/projects", payload);
}

export function updateProject(
  client: ApiClient,
  projectId: string,
  payload: ProjectUpdateInput,
) {
  return client.patch<Project>(`/projects/${projectId}`, payload);
}

export function archiveProject(client: ApiClient, projectId: string) {
  return client.delete<Project>(`/projects/${projectId}`);
}

export function listCategories(client: ApiClient, activeOnly = true) {
  return client.get<Category[]>(
    `/categories${toQuery({ active_only: activeOnly ? "true" : "false" })}`,
  );
}

export function createCategory(client: ApiClient, payload: CategoryCreateInput) {
  return client.post<Category>("/categories", payload);
}

export function listTags(client: ApiClient) {
  return client.get<Tag[]>("/tags");
}

export function createTag(client: ApiClient, payload: TagCreateInput) {
  return client.post<Tag>("/tags", payload);
}

export function listProjectKnowledgePacks(
  client: ApiClient,
  projectId: string,
  params: { page?: number; page_size?: number; status?: string; search?: string } = {},
) {
  return client.get<KnowledgePackListResponse>(
    `/projects/${projectId}/knowledge-packs${toQuery(params)}`,
  );
}

export function createKnowledgePack(
  client: ApiClient,
  projectId: string,
  payload: KnowledgePackCreateInput,
) {
  return client.post<KnowledgePackDetail>(
    `/projects/${projectId}/knowledge-packs`,
    payload,
  );
}

export function getKnowledgePack(client: ApiClient, knowledgePackId: string) {
  return client.get<KnowledgePackDetail>(`/knowledge-packs/${knowledgePackId}`);
}

export function updateKnowledgePackSection(
  client: ApiClient,
  knowledgePackId: string,
  sectionKey: string,
  payload: KnowledgePackSectionUpdateInput,
) {
  return client.patch<KnowledgePackSection>(
    `/knowledge-packs/${knowledgePackId}/sections/${sectionKey}`,
    payload,
  );
}

export function listProjectScripts(
  client: ApiClient,
  projectId: string,
  params: { page?: number; page_size?: number; status?: string; search?: string } = {},
) {
  return client.get<ScriptListResponse>(
    `/projects/${projectId}/scripts${toQuery(params)}`,
  );
}

export function createScript(
  client: ApiClient,
  projectId: string,
  payload: ScriptCreateInput,
) {
  return client.post<ScriptSummary>(`/projects/${projectId}/scripts`, payload);
}

export async function getLatestContentVersion(
  client: ApiClient,
  projectId: string,
): Promise<ContentVersionSummary | null> {
  try {
    return await client.get<ContentVersionSummary>(
      `/projects/${projectId}/content-versions/latest`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function getApprovedContentVersion(
  client: ApiClient,
  projectId: string,
): Promise<ContentVersionSummary | null> {
  try {
    return await client.get<ContentVersionSummary>(
      `/projects/${projectId}/content-versions/approved`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function getWorkflowStatus(client: ApiClient, scriptId: string) {
  return client.get<WorkflowStatus>(`/scripts/${scriptId}/workflow/status`);
}
