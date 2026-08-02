import { ApiError, type ApiClient } from "@/lib/api/client";
import type {
  ApprovalActionInput,
  ApprovalDetail,
  ApprovalListParams,
  ApprovalListResponse,
  ApprovalRecord,
  ApprovalRejectInput,
  ContentVersionSummary,
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

export function listApprovals(
  client: ApiClient,
  params: ApprovalListParams = {},
) {
  return client.get<ApprovalListResponse>(
    `/approvals${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
      project_id: params.project_id,
      search: params.search,
    })}`,
  );
}

export function getApprovalDetail(client: ApiClient, approvalId: string) {
  return client.get<ApprovalDetail>(`/approvals/${approvalId}`);
}

export function approveApproval(
  client: ApiClient,
  approvalId: string,
  payload: ApprovalActionInput = {},
) {
  return client.post<ApprovalRecord>(
    `/approvals/${approvalId}/approve`,
    payload,
  );
}

export function rejectApproval(
  client: ApiClient,
  approvalId: string,
  payload: ApprovalRejectInput,
) {
  return client.post<ApprovalRecord>(
    `/approvals/${approvalId}/reject`,
    payload,
  );
}

export function cancelApproval(
  client: ApiClient,
  approvalId: string,
  payload: ApprovalActionInput = {},
) {
  return client.post<ApprovalRecord>(
    `/approvals/${approvalId}/cancel`,
    payload,
  );
}

export function listVersionApprovals(client: ApiClient, versionId: string) {
  return client.get<ApprovalRecord[]>(
    `/content-versions/${versionId}/approvals`,
  );
}

export async function getScriptLatestVersion(
  client: ApiClient,
  scriptId: string,
): Promise<ContentVersionSummary | null> {
  try {
    return await client.get<ContentVersionSummary>(
      `/scripts/${scriptId}/content-versions/latest`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function getScriptApprovedVersion(
  client: ApiClient,
  scriptId: string,
): Promise<ContentVersionSummary | null> {
  try {
    return await client.get<ContentVersionSummary>(
      `/scripts/${scriptId}/content-versions/approved`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function listScriptContentVersions(
  client: ApiClient,
  scriptId: string,
  params: { page?: number; page_size?: number; status?: string } = {},
) {
  return client.get<{
    items: ContentVersionSummary[];
    page: number;
    page_size: number;
    total: number;
  }>(
    `/scripts/${scriptId}/content-versions${toQuery({
      page: params.page,
      page_size: params.page_size,
      status: params.status,
    })}`,
  );
}
