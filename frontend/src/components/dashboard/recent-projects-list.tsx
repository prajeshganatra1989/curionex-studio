import Link from "next/link";

import { StatusBadge } from "@/components/ui/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { RecentProject } from "@/lib/dashboard/types";
import { formatRelativeTime, initials } from "@/lib/utils";

type RecentProjectsListProps = {
  projects: RecentProject[];
};

export function RecentProjectsList({ projects }: RecentProjectsListProps) {
  if (projects.length === 0) {
    return (
      <EmptyState
        title="No projects yet"
        description="Create your first project to start producing scripts."
      />
    );
  }

  return (
    <ul className="divide-y divide-border">
      {projects.map((project) => (
        <li key={project.id}>
          <Link
            href={`/projects/${project.id}`}
            className="flex items-center gap-3 rounded-md px-2 py-3 transition hover:bg-surface-hover"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface-elevated text-xs font-semibold text-brand-orange">
              {initials(project.name)}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium text-foreground">
                  {project.name}
                </span>
                <StatusBadge status={project.status} />
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                <span className="font-mono text-[11px] text-brand-amber">
                  {project.projectCode}
                </span>
                {project.category ? ` · ${project.category}` : ""}
              </p>
            </div>
            <time
              className="shrink-0 text-xs text-muted-foreground"
              dateTime={project.updatedAt}
            >
              {formatRelativeTime(project.updatedAt)}
            </time>
          </Link>
        </li>
      ))}
    </ul>
  );
}
