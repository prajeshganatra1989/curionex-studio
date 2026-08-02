"use client";

import Link from "next/link";
import { memo } from "react";
import { BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { ApiError } from "@/lib/api/client";
import { useKnowledgePack } from "@/lib/knowledge-packs/hooks";
import { SECTION_ORDER } from "@/lib/knowledge-packs/sections";

const CONTEXT_KEYS = [
  "research",
  "facts",
  "sources",
  "audience",
  "content_angle",
  "key_insights",
] as const;

type KnowledgePackContextPanelProps = {
  projectId: string;
  knowledgePackId: string | null;
  onAssociate: () => void;
};

function summarize(content: string, max = 160): string {
  const trimmed = content.trim();
  if (!trimmed) return "No notes yet.";
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max).trim()}…`;
}

export const KnowledgePackContextPanel = memo(function KnowledgePackContextPanel({
  projectId,
  knowledgePackId,
  onAssociate,
}: KnowledgePackContextPanelProps) {
  const packQuery = useKnowledgePack(knowledgePackId ?? "");

  if (!knowledgePackId) {
    return (
      <aside
        className="rounded-xl border border-border/70 bg-surface/60 p-4"
        data-testid="kp-context-empty"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Knowledge Pack
        </p>
        <EmptyState
          title="No Knowledge Pack linked"
          description="Associate a pack from this project for research context while you write."
          action={
            <Button type="button" variant="secondary" onClick={onAssociate}>
              Associate Knowledge Pack
            </Button>
          }
        />
      </aside>
    );
  }

  if (packQuery.isLoading) {
    return (
      <div data-testid="kp-context-loading">
        <LoadingSkeleton className="h-64" />
      </div>
    );
  }

  if (packQuery.isError || !packQuery.data) {
    return (
      <ErrorState
        message={
          packQuery.error instanceof ApiError
            ? packQuery.error.detail
            : "Unable to load Knowledge Pack."
        }
        action={
          <button
            type="button"
            className="text-sm text-brand-orange underline"
            onClick={() => void packQuery.refetch()}
          >
            Try again
          </button>
        }
      />
    );
  }

  const pack = packQuery.data;

  return (
    <aside
      className="space-y-4 rounded-xl border border-border/70 bg-surface/60 p-4"
      data-testid="kp-context-panel"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Knowledge Pack
          </p>
          <p className="mt-1 truncate font-medium text-foreground">{pack.name}</p>
        </div>
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border text-brand-orange">
          <BookOpen className="h-4 w-4" aria-hidden />
        </span>
      </div>

      <ul className="space-y-3">
        {CONTEXT_KEYS.map((key) => {
          const meta = SECTION_ORDER.find((s) => s.key === key);
          const section = pack.sections.find((s) => s.section_key === key);
          return (
            <li key={key}>
              <p className="text-xs font-medium text-foreground">
                {meta?.title ?? key}
              </p>
              <p className="mt-0.5 whitespace-pre-wrap text-xs leading-relaxed text-muted-foreground">
                {summarize(section?.content ?? "")}
              </p>
            </li>
          );
        })}
      </ul>

      <Link
        href={`/projects/${projectId}/knowledge-packs/${pack.id}`}
        className="inline-flex text-sm text-brand-orange underline-offset-2 hover:underline"
      >
        Open Knowledge Pack
      </Link>
    </aside>
  );
});
