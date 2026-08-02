"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getActiveContentStandard,
  getContentStandardSummary,
  listContentStandards,
} from "@/lib/api/content-standards";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";

export const contentStandardKeys = {
  all: ["content-standards"] as const,
  list: (params?: { status?: string; include_archived?: boolean }) =>
    [...contentStandardKeys.all, "list", params ?? {}] as const,
  active: () => [...contentStandardKeys.all, "active"] as const,
  summary: () => [...contentStandardKeys.all, "summary"] as const,
};

export function useContentStandardSummary(options?: { enabled?: boolean }) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: contentStandardKeys.summary(),
    queryFn: () => getContentStandardSummary(api),
    enabled: status === "authenticated" && (options?.enabled ?? true),
  });
}

export function useActiveContentStandard(options?: { enabled?: boolean }) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: contentStandardKeys.active(),
    queryFn: () => getActiveContentStandard(api),
    enabled: status === "authenticated" && (options?.enabled ?? true),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 2;
    },
  });
}

export function useContentStandards(params?: {
  status?: string;
  include_archived?: boolean;
}) {
  const { api, status } = useAuth();
  return useQuery({
    queryKey: contentStandardKeys.list(params),
    queryFn: () => listContentStandards(api, params),
    enabled: status === "authenticated",
  });
}
