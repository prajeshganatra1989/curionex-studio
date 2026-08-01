"use client";

import Link from "next/link";
import { ChevronDown, Plus } from "lucide-react";

import { BrandLogo } from "@/components/brand/brand-logo";
import { SidebarNavigation } from "@/components/layout/sidebar-navigation";
import { AvatarInitials } from "@/components/ui/avatar-initials";
import { useAuth } from "@/lib/auth/auth-context";
import { cn } from "@/lib/utils";

type SidebarProps = {
  className?: string;
  onNavigate?: () => void;
};

export function Sidebar({ className, onNavigate }: SidebarProps) {
  const { user } = useAuth();
  const displayName = user
    ? `${user.first_name} ${user.last_name}`.trim()
    : "Curionex user";

  return (
    <aside
      className={cn(
        "flex h-full w-[var(--sidebar-width)] flex-col border-r border-border bg-surface",
        className,
      )}
    >
      <div className="border-b border-border px-4 py-5">
        <BrandLogo priority />
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <SidebarNavigation onNavigate={onNavigate} />
      </div>

      <div className="space-y-3 border-t border-border p-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-surface-elevated p-2.5">
          <AvatarInitials name={displayName} className="h-10 w-10" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-foreground">
              {displayName}
            </p>
            <p className="truncate text-xs font-medium text-brand-orange">
              Owner
            </p>
          </div>
          <ChevronDown
            className="h-4 w-4 shrink-0 text-muted-foreground"
            aria-hidden
          />
        </div>
        <Link
          href="/scripts"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-xl border border-border bg-surface-elevated p-2.5 transition hover:border-brand-orange/40 hover:bg-surface-hover"
        >
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-gradient text-black shadow-[var(--glow-brand)]">
            <Plus className="h-5 w-5" aria-hidden />
          </span>
          <span className="min-w-0 text-left">
            <span className="block text-sm font-semibold text-foreground">
              New Script
            </span>
            <span className="block text-xs text-muted-foreground">
              Create a new script
            </span>
          </span>
        </Link>
      </div>
    </aside>
  );
}
