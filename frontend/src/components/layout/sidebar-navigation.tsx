"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MAIN_NAV } from "@/components/layout/navigation";
import { cn } from "@/lib/utils";

type SidebarNavigationProps = {
  onNavigate?: () => void;
};

export function SidebarNavigation({ onNavigate }: SidebarNavigationProps) {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-1 px-3">
      {MAIN_NAV.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-surface-hover hover:text-foreground",
              active && "nav-active",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
