import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";
import { RedirectIfAuthenticated } from "@/components/auth/route-guards";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export const metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return (
    <RedirectIfAuthenticated>
      <div className="login-atmosphere flex min-h-screen items-center justify-center px-4 py-10">
        <Suspense fallback={<LoadingSkeleton className="h-80 w-full max-w-md" />}>
          <LoginForm />
        </Suspense>
      </div>
    </RedirectIfAuthenticated>
  );
}
