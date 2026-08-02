"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getProductionActivity,
  getProductionMetrics,
  getProductionOverview,
  getProductionQueue,
  getProductionSession,
  getProductionSettings,
  updateProductionSettings,
} from "@/lib/api/production";
import { useAuth } from "@/lib/auth/auth-context";
import type {
  MetricsRange,
  ProductionQueueParams,
  ProductionSettingsUpdate,
} from "@/lib/production/types";

export const productionKeys = {
  all: ["production"] as const,
  overview: () => [...productionKeys.all, "overview"] as const,
  session: () => [...productionKeys.all, "session"] as const,
  queues: () => [...productionKeys.all, "queue"] as const,
  queue: (params: ProductionQueueParams) =>
    [...productionKeys.queues(), params] as const,
  metrics: (range: MetricsRange) =>
    [...productionKeys.all, "metrics", range] as const,
  activity: (limit: number) =>
    [...productionKeys.all, "activity", limit] as const,
  settings: () => [...productionKeys.all, "settings"] as const,
};

const OVERVIEW_POLL_MS = 30_000;
const SESSION_POLL_MS = 20_000;

export function useProductionOverview(options?: { poll?: boolean }) {
  const { api, status } = useAuth();
  const poll = options?.poll ?? true;
  return useQuery({
    queryKey: productionKeys.overview(),
    queryFn: () => getProductionOverview(api),
    enabled: status === "authenticated",
    refetchInterval: poll ? OVERVIEW_POLL_MS : false,
    refetchIntervalInBackground: false,
  });
}

export function useProductionSession(options?: { poll?: boolean }) {
  const { api, status } = useAuth();
  const poll = options?.poll ?? true;
  return useQuery({
    queryKey: productionKeys.session(),
    queryFn: () => getProductionSession(api),
    enabled: status === "authenticated",
    refetchInterval: poll ? SESSION_POLL_MS : false,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  });
}

export function useProductionQueue(params: ProductionQueueParams) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: productionKeys.queue(params),
    queryFn: () => getProductionQueue(api, params),
    enabled: status === "authenticated",
  });
}

export function useProductionMetrics(range: MetricsRange = "7d") {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: productionKeys.metrics(range),
    queryFn: () => getProductionMetrics(api, range),
    enabled: status === "authenticated",
  });
}

export function useProductionActivity(limit = 20) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: productionKeys.activity(limit),
    queryFn: () => getProductionActivity(api, limit),
    enabled: status === "authenticated",
  });
}

export function useProductionSettings(enabled = true) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: productionKeys.settings(),
    queryFn: () => getProductionSettings(api),
    enabled: status === "authenticated" && enabled,
  });
}

export function useUpdateProductionSettings() {
  const { api } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProductionSettingsUpdate) =>
      updateProductionSettings(api, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: productionKeys.all });
    },
  });
}
