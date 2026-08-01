"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/auth-context";
import { tokenStore } from "@/lib/auth/token-store";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

function AuthLoading({ label = "Loading Curionex Studio…" }: { label?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm space-y-3 text-center">
        <LoadingSkeleton className="mx-auto h-10 w-48" />
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status !== "unauthenticated") return;
    tokenStore.clear();
    const next = encodeURIComponent(pathname || "/dashboard");
    // Hard navigation breaks any stale cookie ↔ client redirect loop.
    window.location.replace(`/login?next=${next}`);
  }, [status, pathname]);

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status !== "authenticated") {
    return <AuthLoading label="Redirecting to sign in…" />;
  }

  return <>{children}</>;
}

export function RedirectIfAuthenticated({
  children,
}: {
  children: React.ReactNode;
}) {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [status, router]);

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status === "authenticated") {
    return <AuthLoading label="Opening dashboard…" />;
  }

  return <>{children}</>;
}
