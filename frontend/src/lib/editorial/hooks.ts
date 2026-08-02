"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  archiveEditorialTopic,
  createEditorialTopic,
  createProjectFromTopic,
  getEditorialTopicSummary,
  listEditorialTopics,
} from "@/lib/api/editorial";
import { useAuth } from "@/lib/auth/auth-context";
import type {
  CreateProjectFromTopicInput,
  EditorialTopicCreateInput,
  EditorialTopicListParams,
} from "@/lib/editorial/types";
import { projectKeys } from "@/lib/projects/hooks";
import { productionKeys } from "@/lib/production/hooks";

export const editorialKeys = {
  all: ["editorial-topics"] as const,
  lists: () => [...editorialKeys.all, "list"] as const,
  list: (params: EditorialTopicListParams) =>
    [...editorialKeys.lists(), params] as const,
  summary: () => [...editorialKeys.all, "summary"] as const,
};

export function useEditorialTopics(params: EditorialTopicListParams = {}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: editorialKeys.list(params),
    queryFn: () => listEditorialTopics(api, params),
    enabled: status === "authenticated",
  });
}

export function useEditorialTopicSummary(options?: { enabled?: boolean }) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: editorialKeys.summary(),
    queryFn: () => getEditorialTopicSummary(api),
    enabled: status === "authenticated" && (options?.enabled ?? true),
  });
}

export function useCreateEditorialTopic() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EditorialTopicCreateInput) =>
      createEditorialTopic(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: editorialKeys.all });
    },
  });
}

export function useArchiveEditorialTopic() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (topicId: string) => archiveEditorialTopic(api, topicId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: editorialKeys.all });
    },
  });
}

export function useCreateProjectFromTopic() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      topicId,
      payload,
    }: {
      topicId: string;
      payload?: CreateProjectFromTopicInput;
    }) => createProjectFromTopic(api, topicId, payload ?? {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: editorialKeys.all });
      void qc.invalidateQueries({ queryKey: projectKeys.all });
      void qc.invalidateQueries({ queryKey: productionKeys.all });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
