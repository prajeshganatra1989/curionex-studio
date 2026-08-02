"use client";

import Link from "next/link";
import { CirclePlay } from "lucide-react";

import { PageContainer } from "@/components/layout/page-header";
import { useAuth } from "@/lib/auth/auth-context";
import { greetingForHour } from "@/lib/utils";

export function DashboardPage() {
  const { user, status } = useAuth();
  const hour = new Date().getHours();
  const greeting = greetingForHour(hour);
  const firstName = user?.first_name ?? "there";

  if (status === "loading") {
    return (
      <PageContainer>
        <div className="h-40 animate-pulse rounded-2xl bg-surface" />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div
        className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center text-center"
        data-testid="dashboard-session-launch"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-amber">
          Curionex Studio
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          {greeting}, {firstName}
        </h1>
        <p className="mt-3 max-w-md text-sm text-muted-foreground sm:text-base">
          Skip the noise. Open your Production Session and continue the next
          Shorts workflow step.
        </p>
        <Link
          href="/production/session"
          data-testid="open-production-session"
          className="mt-8 inline-flex items-center gap-2 rounded-xl bg-brand-orange px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90"
        >
          <CirclePlay className="h-4 w-4" aria-hidden />
          Open Production Session
        </Link>
      </div>
    </PageContainer>
  );
}
