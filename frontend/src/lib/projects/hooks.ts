"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { useAuth } from "@/lib/auth/auth-context";
import {
  archiveProject,
  createCategory,
  createKnowledgePack,
  createProject,
  createScript,
  createTag,
  getApprovedContentVersion,
  getLatestContentVersion,
  getProject,
  getWorkflowStatus,
  listCategories,
  listProjectKnowledgePacks,
  listProjectScripts,
  listProjects,
  listTags,
  updateProject,
} from "@/lib/api/projects";
import type {
  CategoryCreateInput,
  KnowledgePackCreateInput,
  ProjectCreateInput,
  ProjectListParams,
  ProjectUpdateInput,
  ScriptCreateInput,
  TagCreateInput,
} from "@/lib/api/types";

export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (params: ProjectListParams) => [...projectKeys.lists(), params] as const,
  details: () => [...projectKeys.all, "detail"] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
  packs: (id: string) => [...projectKeys.detail(id), "packs"] as const,
  scripts: (id: string) => [...projectKeys.detail(id), "scripts"] as const,
  versions: (id: string) => [...projectKeys.detail(id), "versions"] as const,
};

export const taxonomyKeys = {
  categories: ["categories"] as const,
  tags: ["tags"] as const,
};

export function useProjects(params: ProjectListParams) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => listProjects(api, params),
    enabled: status === "authenticated",
  });
}

export function useProject(projectId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => getProject(api, projectId),
    enabled: status === "authenticated" && Boolean(projectId),
  });
}

export function useCategories(activeOnly = true) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: [...taxonomyKeys.categories, activeOnly],
    queryFn: () => listCategories(api, activeOnly),
    enabled: status === "authenticated",
    staleTime: 60_000,
  });
}

export function useTags() {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: taxonomyKeys.tags,
    queryFn: () => listTags(api),
    enabled: status === "authenticated",
    staleTime: 60_000,
  });
}

export function useCreateProject() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectCreateInput) => createProject(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

export function useUpdateProject(projectId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectUpdateInput) =>
      updateProject(api, projectId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: projectKeys.all });
      void qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useArchiveProject() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => archiveProject(api, projectId),
    onSuccess: (_data, projectId) => {
      void qc.invalidateQueries({ queryKey: projectKeys.all });
      void qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useCreateCategory() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CategoryCreateInput) => createCategory(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: taxonomyKeys.categories });
    },
  });
}

export function useCreateTag() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TagCreateInput) => createTag(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: taxonomyKeys.tags });
    },
  });
}

export function useProjectKnowledgePacks(projectId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: projectKeys.packs(projectId),
    queryFn: () =>
      listProjectKnowledgePacks(api, projectId, { page: 1, page_size: 5 }),
    enabled: status === "authenticated" && Boolean(projectId),
  });
}

export function useProjectScripts(projectId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: projectKeys.scripts(projectId),
    queryFn: () => listProjectScripts(api, projectId, { page: 1, page_size: 5 }),
    enabled: status === "authenticated" && Boolean(projectId),
  });
}

export function useProjectVersions(projectId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: projectKeys.versions(projectId),
    queryFn: async () => {
      const [latest, approved] = await Promise.all([
        getLatestContentVersion(api, projectId),
        getApprovedContentVersion(api, projectId),
      ]);
      return { latest, approved };
    },
    enabled: status === "authenticated" && Boolean(projectId),
  });
}

export function useCreateKnowledgePack(projectId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnowledgePackCreateInput) =>
      createKnowledgePack(api, projectId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: projectKeys.packs(projectId) });
    },
  });
}

export function useCreateScript(projectId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScriptCreateInput) =>
      createScript(api, projectId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: projectKeys.scripts(projectId) });
    },
  });
}

export function useScriptWorkflowStatus(scriptId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: ["workflow-status", scriptId],
    queryFn: () => getWorkflowStatus(api, scriptId!),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}
