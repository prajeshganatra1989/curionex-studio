import type { ApiClient } from "@/lib/api/client";
import type {
  ContentStandard,
  ContentStandardListResponse,
  ContentStandardSummary,
} from "@/lib/editorial/content-standard-types";

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

export function listContentStandards(
  client: ApiClient,
  params: { status?: string; include_archived?: boolean } = {},
) {
  return client.get<ContentStandardListResponse>(
    `/content-standards${toQuery({
      status: params.status,
      include_archived: params.include_archived,
    })}`,
  );
}

export function getActiveContentStandard(client: ApiClient) {
  return client.get<ContentStandard>("/content-standards/active");
}

export function getContentStandardSummary(client: ApiClient) {
  return client.get<ContentStandardSummary>("/content-standards/summary");
}

export function getContentStandard(client: ApiClient, standardId: string) {
  return client.get<ContentStandard>(`/content-standards/${standardId}`);
}
