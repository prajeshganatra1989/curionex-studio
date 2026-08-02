import type { ApiClient } from "@/lib/api/client";
import type {
  MetricsRange,
  ProductionActivityResponse,
  ProductionMetrics,
  ProductionOverview,
  ProductionQueueParams,
  ProductionQueueResponse,
  ProductionSession,
  ProductionSettings,
  ProductionSettingsUpdate,
} from "@/lib/production/types";

function toQuery(params: Record<string, string | number | boolean | undefined | null>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function getProductionOverview(client: ApiClient) {
  return client.get<ProductionOverview>("/production/overview");
}

export function getProductionSession(client: ApiClient) {
  return client.get<ProductionSession>("/production/session");
}

export function getProductionQueue(
  client: ApiClient,
  params: ProductionQueueParams = {},
) {
  return client.get<ProductionQueueResponse>(
    `/production/queue${toQuery({
      page: params.page,
      page_size: params.page_size,
      production_stage: params.production_stage,
      project_id: params.project_id,
      category_id: params.category_id,
      tag_id: params.tag_id,
      search: params.search,
      quality_band: params.quality_band,
      ai_job_status: params.ai_job_status,
      stale_quality: params.stale_quality,
      blocked_only: params.blocked_only,
      pending_approval: params.pending_approval,
      script_status: params.script_status,
      sort: params.sort,
    })}`,
  );
}

export function getProductionMetrics(
  client: ApiClient,
  range: MetricsRange = "7d",
) {
  return client.get<ProductionMetrics>(
    `/production/metrics${toQuery({ range })}`,
  );
}

export function getProductionActivity(client: ApiClient, limit = 20) {
  return client.get<ProductionActivityResponse>(
    `/production/activity${toQuery({ limit })}`,
  );
}

export function getProductionSettings(client: ApiClient) {
  return client.get<ProductionSettings>("/production/settings");
}

export function updateProductionSettings(
  client: ApiClient,
  payload: ProductionSettingsUpdate,
) {
  return client.patch<ProductionSettings>("/production/settings", payload);
}
