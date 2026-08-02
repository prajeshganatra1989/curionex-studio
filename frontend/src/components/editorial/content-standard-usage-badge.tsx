"use client";

import { useContentStandardSummary } from "@/lib/editorial/content-standard-hooks";

export function ContentStandardUsageBadge() {
  const summaryQuery = useContentStandardSummary();
  const summary = summaryQuery.data;

  if (summaryQuery.isLoading) {
    return (
      <p
        className="text-sm text-muted-foreground"
        data-testid="content-standard-usage"
      >
        Uses: loading Content Standard…
      </p>
    );
  }

  if (!summary?.has_active || !summary.label) {
    return (
      <p
        className="text-sm text-muted-foreground"
        data-testid="content-standard-usage"
      >
        Uses: no active Content Standard
      </p>
    );
  }

  return (
    <p
      className="text-sm text-foreground"
      data-testid="content-standard-usage"
    >
      Uses:{" "}
      <span className="font-medium text-brand-orange">{summary.label}</span>
    </p>
  );
}
