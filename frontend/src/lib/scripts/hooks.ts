"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  archiveScript,
  createWorkflowVersion,
  createProductionPackage,
  getContentVersion,
  getProductionPackageEligibility,
  getScript,
  getScriptWorkflow,
  getWorkflowStatus,
  listScriptDocuments,
  submitWorkflowReview,
  updateScript,
  updateScriptDocument,
} from "@/lib/api/projects";
import { listScriptContentVersions } from "@/lib/api/approvals";
import type {
  ScriptDocumentUpdateInput,
  ScriptUpdateInput,
} from "@/lib/api/types";
import { useAuth } from "@/lib/auth/auth-context";
import { knowledgePackKeys } from "@/lib/knowledge-packs/hooks";
import { projectKeys, useProjectScripts } from "@/lib/projects/hooks";

export { useProjectScripts };

export const scriptKeys = {
  all: ["scripts"] as const,
  detail: (scriptId: string) => [...scriptKeys.all, "detail", scriptId] as const,
  documents: (scriptId: string) =>
    [...scriptKeys.detail(scriptId), "documents"] as const,
  workflow: (scriptId: string) =>
    [...scriptKeys.detail(scriptId), "workflow"] as const,
  workflowStatus: (scriptId: string) =>
    [...scriptKeys.detail(scriptId), "workflow-status"] as const,
  versions: (scriptId: string) =>
    [...scriptKeys.all, "versions", scriptId] as const,
  versionDetail: (versionId: string) =>
    [...scriptKeys.all, "version", versionId] as const,
  productionEligibility: (scriptId: string) =>
    [...scriptKeys.detail(scriptId), "production-eligibility"] as const,
  productionPackage: (scriptId: string) =>
    [...scriptKeys.detail(scriptId), "production-package"] as const,
};

export function useScript(scriptId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.detail(scriptId),
    queryFn: () => getScript(api, scriptId),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useScriptDocuments(scriptId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.documents(scriptId),
    queryFn: () => listScriptDocuments(api, scriptId),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useUpdateScript(scriptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScriptUpdateInput) =>
      updateScript(api, scriptId, payload),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });
      void qc.invalidateQueries({
        queryKey: projectKeys.scripts(data.project_id),
      });
      if (data.knowledge_pack_id) {
        void qc.invalidateQueries({
          queryKey: knowledgePackKeys.detail(data.knowledge_pack_id),
        });
      }
    },
  });
}

export function useUpdateScriptDocument(scriptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      documentType,
      payload,
    }: {
      documentType: string;
      payload: ScriptDocumentUpdateInput;
    }) => updateScriptDocument(api, scriptId, documentType, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });
      void qc.invalidateQueries({ queryKey: scriptKeys.documents(scriptId) });
    },
  });
}

export function useArchiveScript(projectId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (scriptId: string) => archiveScript(api, scriptId),
    onSuccess: (_data, scriptId) => {
      void qc.invalidateQueries({ queryKey: projectKeys.scripts(projectId) });
      void qc.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });
    },
  });
}

export function useScriptWorkflow(scriptId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.workflow(scriptId),
    queryFn: () => getScriptWorkflow(api, scriptId),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useScriptWorkflowStatus(scriptId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.workflowStatus(scriptId ?? ""),
    queryFn: () => getWorkflowStatus(api, scriptId!),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useCreateWorkflowVersion(scriptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => createWorkflowVersion(api, scriptId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });
      void qc.invalidateQueries({ queryKey: scriptKeys.workflow(scriptId) });
      void qc.invalidateQueries({
        queryKey: scriptKeys.workflowStatus(scriptId),
      });
      void qc.invalidateQueries({ queryKey: scriptKeys.all });
    },
  });
}

export function useSubmitWorkflowReview(scriptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => submitWorkflowReview(api, scriptId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: scriptKeys.detail(scriptId) });
      void qc.invalidateQueries({ queryKey: scriptKeys.workflow(scriptId) });
      void qc.invalidateQueries({
        queryKey: scriptKeys.workflowStatus(scriptId),
      });
      void qc.invalidateQueries({ queryKey: ["reviews"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useScriptVersions(scriptId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.versions(scriptId),
    queryFn: () =>
      listScriptContentVersions(api, scriptId, {
        page: 1,
        page_size: 100,
      }),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useContentVersion(versionId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.versionDetail(versionId ?? ""),
    queryFn: () => getContentVersion(api, versionId!),
    enabled: status === "authenticated" && Boolean(versionId),
  });
}

export function useProductionPackageEligibility(scriptId: string) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.productionEligibility(scriptId),
    queryFn: () => getProductionPackageEligibility(api, scriptId),
    enabled: status === "authenticated" && Boolean(scriptId),
  });
}

export function useCreateProductionPackage(scriptId: string) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => createProductionPackage(api, scriptId),
    onSuccess: (data) => {
      qc.setQueryData(scriptKeys.productionPackage(scriptId), data);
      void qc.invalidateQueries({
        queryKey: scriptKeys.productionEligibility(scriptId),
      });
    },
  });
}

export function useProductionPackage(scriptId: string, enabled = false) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: scriptKeys.productionPackage(scriptId),
    queryFn: () => createProductionPackage(api, scriptId),
    enabled: status === "authenticated" && Boolean(scriptId) && enabled,
    staleTime: 60_000,
  });
}
