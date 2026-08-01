"use client";

import { useState } from "react";
import { Menu, X } from "lucide-react";

import { BrandMark } from "@/components/brand/brand-logo";
import { Sidebar } from "@/components/layout/sidebar";
import {
  GlobalSearch,
  HelpButton,
  NotificationButton,
  UserMenu,
} from "@/components/layout/top-header";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-[var(--sidebar-width)]">
        <Sidebar />
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/60"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative h-full w-[min(100%,var(--sidebar-width))] shadow-[var(--shadow-panel)] transition duration-200">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      ) : null}

      <div className="flex min-h-screen flex-1 flex-col lg:pl-[var(--sidebar-width)]">
        <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
          <div className="flex items-center gap-3 px-4 py-3 sm:px-6">
            <button
              type="button"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-foreground lg:hidden"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              onClick={() => setMobileOpen((value) => !value)}
            >
              {mobileOpen ? (
                <X className="h-4 w-4" />
              ) : (
                <Menu className="h-4 w-4" />
              )}
            </button>
            <div className="lg:hidden">
              <BrandMark size={28} />
            </div>
            <div className="hidden flex-1 sm:block">
              <GlobalSearch />
            </div>
            <div className="ml-auto flex items-center gap-2">
              <HelpButton />
              <NotificationButton />
              <UserMenu />
            </div>
          </div>
          <div className="border-t border-border px-4 py-2 sm:hidden">
            <GlobalSearch />
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
