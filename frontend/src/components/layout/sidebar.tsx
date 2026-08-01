"use client";

import Link from "next/link";
import { Plus } from "lucide-react";

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
      <div className="flex items-center gap-3 px-4 py-5">
        <BrandLogo className="h-11" priority />
      </div>

      <div className="flex-1 overflow-y-auto pb-4">
        <SidebarNavigation onNavigate={onNavigate} />
      </div>

      <div className="space-y-3 border-t border-border p-4">
        <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-elevated p-2.5">
          <AvatarInitials name={displayName} />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-foreground">
              {displayName}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {user?.email ?? "Signed in"}
            </p>
          </div>
        </div>
        <Link
          href="/scripts"
          onClick={onNavigate}
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-brand-gradient px-4 text-sm font-semibold text-black shadow-[var(--glow-brand)] transition hover:brightness-110"
        >
          <Plus className="h-4 w-4" aria-hidden />
          New Script
        </Link>
      </div>
    </aside>
  );
}
