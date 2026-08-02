"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  approveApproval,
  cancelApproval,
  getApprovalDetail,
  listApprovals,
  rejectApproval,
} from "@/lib/api/approvals";
import type {
  ApprovalActionInput,
  ApprovalListParams,
  ApprovalRejectInput,
} from "@/lib/api/types";
import { useAuth } from "@/lib/auth/auth-context";
import { scriptKeys } from "@/lib/scripts/hooks";

export const reviewKeys = {
  all: ["reviews"] as const,
  list: (params: ApprovalListParams) =>
    [...reviewKeys.all, "list", params] as const,
  detail: (approvalId: string) =>
    [...reviewKeys.all, "detail", approvalId] as const,
};

export function useReviews(params: ApprovalListParams = {}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: reviewKeys.list(params),
    queryFn: () => listApprovals(api, params),
    enabled: status === "authenticated",
  });
}

export function useApproval(approvalId: string | null) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: reviewKeys.detail(approvalId ?? ""),
    queryFn: () => getApprovalDetail(api, approvalId!),
    enabled: status === "authenticated" && Boolean(approvalId),
  });
}

function invalidateReviewQueries(
  qc: ReturnType<typeof useQueryClient>,
  approvalId: string,
  scriptId?: string | null,
) {
  void qc.invalidateQueries({ queryKey: reviewKeys.all });
  void qc.invalidateQueries({ queryKey: reviewKeys.detail(approvalId) });
  void qc.invalidateQueries({ queryKey: ["dashboard"] });
  if (scriptId) {
    void qc.invalidateQueries({ queryKey: scriptKeys.workflow(scriptId) });
    void qc.invalidateQueries({
      queryKey: scriptKeys.workflowStatus(scriptId),
    });
    void qc.invalidateQueries({
      queryKey: scriptKeys.versions(scriptId),
    });
  }
}

export function useApproveApproval(approvalId: string, scriptId?: string | null) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApprovalActionInput = {}) =>
      approveApproval(api, approvalId, payload),
    onSuccess: () => invalidateReviewQueries(qc, approvalId, scriptId),
  });
}

export function useRejectApproval(approvalId: string, scriptId?: string | null) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApprovalRejectInput) =>
      rejectApproval(api, approvalId, payload),
    onSuccess: () => invalidateReviewQueries(qc, approvalId, scriptId),
  });
}

export function useCancelApproval(approvalId: string, scriptId?: string | null) {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApprovalActionInput = {}) =>
      cancelApproval(api, approvalId, payload),
    onSuccess: () => invalidateReviewQueries(qc, approvalId, scriptId),
  });
}
