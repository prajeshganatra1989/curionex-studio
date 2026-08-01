"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getKnowledgePack,
  updateKnowledgePackSection,
} from "@/lib/api/projects";
import type { KnowledgePackSectionUpdateInput } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/auth-context";
import { projectKeys } from "@/lib/projects/hooks";

export const knowledgePackKeys = {
  all: ["knowledge-packs"] as const,
  detail: (id: string) => [...knowledgePackKeys.all, "detail", id] as const,
};

export function useKnowledgePack(knowledgePackId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: knowledgePackKeys.detail(knowledgePackId),
    queryFn: () => getKnowledgePack(api, knowledgePackId),
    enabled: status === "authenticated" && Boolean(knowledgePackId),
  });
}

export function useUpdateKnowledgePackSection(knowledgePackId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sectionKey,
      payload,
    }: {
      sectionKey: string;
      payload: KnowledgePackSectionUpdateInput;
    }) => updateKnowledgePackSection(api, knowledgePackId, sectionKey, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: knowledgePackKeys.detail(knowledgePackId),
      });
      void qc.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}
