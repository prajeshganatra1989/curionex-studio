"use client";

import Link from "next/link";
import { MoreHorizontal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type { Project } from "@/lib/api/types";
import { formatRelativeTime, initials } from "@/lib/utils";

type ProjectCardProps = {
  project: Project;
  onArchive: (project: Project) => void;
};

export function ProjectCard({ project, onArchive }: ProjectCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <article className="panel flex flex-col p-4 transition hover:border-border-strong hover:bg-surface-elevated">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-xs font-semibold text-brand-orange">
          {initials(project.name)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/projects/${project.id}`}
              className="truncate text-sm font-semibold text-foreground hover:text-brand-amber"
            >
              {project.name}
            </Link>
            <StatusBadge status={project.status} />
          </div>
          <p className="mt-1 font-mono text-[11px] text-brand-amber">
            {project.project_code}
          </p>
        </div>
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-surface hover:text-foreground"
            aria-label={`Actions for ${project.name}`}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
          {menuOpen ? (
            <div
              role="menu"
              className="absolute right-0 z-20 mt-1 w-40 overflow-hidden rounded-lg border border-border bg-surface-elevated shadow-[var(--shadow-panel)]"
            >
              <Link
                role="menuitem"
                href={`/projects/${project.id}`}
                className="block px-3 py-2 text-sm hover:bg-surface-hover"
                onClick={() => setMenuOpen(false)}
              >
                Open Project
              </Link>
              {project.status !== "archived" ? (
                <button
                  type="button"
                  role="menuitem"
                  className="block w-full px-3 py-2 text-left text-sm text-danger hover:bg-surface-hover"
                  onClick={() => {
                    setMenuOpen(false);
                    onArchive(project);
                  }}
                >
                  Archive
                </button>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      {project.description ? (
        <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
          {project.description}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        {project.category ? (
          <span className="rounded-md border border-border px-2 py-0.5">
            {project.category.name}
          </span>
        ) : null}
        {project.tags.slice(0, 3).map((tag) => (
          <span
            key={tag.id}
            className="rounded-md border border-border px-2 py-0.5"
          >
            {tag.name}
          </span>
        ))}
        {project.tags.length > 3 ? (
          <span>+{project.tags.length - 3}</span>
        ) : null}
        <span className="ml-auto">
          Updated {formatRelativeTime(project.updated_at)}
        </span>
      </div>
    </article>
  );
}
