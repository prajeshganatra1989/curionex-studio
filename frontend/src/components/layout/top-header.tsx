"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { HelpCircle, LogOut, UserRound } from "lucide-react";

import { AvatarInitials } from "@/components/ui/avatar-initials";
import { useAuth } from "@/lib/auth/auth-context";
import { cn } from "@/lib/utils";

export function UserMenu() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const name = user
    ? `${user.first_name} ${user.last_name}`.trim()
    : "Account";

  useEffect(() => {
    function onDocClick(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        className="rounded-full focus-visible:outline-none"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="User menu"
        onClick={() => setOpen((value) => !value)}
      >
        <AvatarInitials name={name} className="h-9 w-9" />
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 z-40 mt-2 w-56 overflow-hidden rounded-lg border border-border bg-surface-elevated shadow-[var(--shadow-panel)]"
        >
          <div className="border-b border-border px-3 py-2">
            <p className="truncate text-sm font-medium">{name}</p>
            <p className="truncate text-xs text-muted-foreground">
              {user?.email}
            </p>
          </div>
          <button
            type="button"
            role="menuitem"
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:bg-surface-hover hover:text-foreground"
            onClick={() => {
              setOpen(false);
              router.push("/settings");
            }}
          >
            <UserRound className="h-4 w-4" />
            Settings
          </button>
          <button
            type="button"
            role="menuitem"
            className={cn(
              "flex w-full items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:bg-surface-hover hover:text-foreground",
            )}
            onClick={() => {
              logout();
              setOpen(false);
              router.replace("/login");
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function NotificationButton() {
  return (
    <button
      type="button"
      className="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground hover:bg-surface-hover hover:text-foreground"
      aria-label="Notifications (3 unread, demo)"
    >
      <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-orange px-1 text-[10px] font-semibold text-black">
        3
      </span>
      <span className="sr-only">3 unread notifications</span>
      <svg
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden
      >
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
    </button>
  );
}

export function HelpButton() {
  return (
    <button
      type="button"
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground hover:bg-surface-hover hover:text-foreground"
      aria-label="Help"
    >
      <HelpCircle className="h-4 w-4" />
    </button>
  );
}

export function GlobalSearch() {
  const pathname = usePathname();

  return (
    <button
      type="button"
      className="flex h-9 w-full max-w-md items-center gap-2 rounded-lg border border-border bg-surface px-3 text-left text-sm text-muted-foreground transition hover:border-border-strong hover:bg-surface-hover"
      aria-label="Open search (visual only in this sprint)"
      title="Search is visual-only in Sprint 1"
      data-pathname={pathname}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-4 w-4 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
      <span className="flex-1 truncate">Search anything...</span>
      <kbd className="hidden rounded border border-border bg-surface-elevated px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:inline">
        ⌘K
      </kbd>
    </button>
  );
}
