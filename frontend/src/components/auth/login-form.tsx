"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";

import { BrandLogo } from "@/components/brand/brand-logo";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/error-state";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { cn } from "@/lib/utils";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginValues) {
    setFormError(null);
    try {
      await login(values.email, values.password);
      const next = searchParams.get("next");
      router.replace(next && next.startsWith("/") ? next : "/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.detail);
      } else {
        setFormError("Unable to reach the API. Check that the backend is running.");
      }
    }
  }

  return (
    <form
      className="panel w-full max-w-md space-y-5 p-6 sm:p-8"
      onSubmit={handleSubmit(onSubmit)}
      noValidate
    >
      <div className="flex flex-col items-center gap-3 text-center">
        <BrandLogo className="h-16" priority />
        <div>
          <h1 className="text-xl font-semibold text-foreground">
            Sign in to Curionex Studio
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Build remarkable ideas into unforgettable stories.
          </p>
        </div>
      </div>

      {formError ? <ErrorState message={formError} title="Sign-in failed" /> : null}

      <div className="space-y-2">
        <label htmlFor="email" className="text-sm font-medium text-foreground">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          className={cn(
            "h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground",
            errors.email && "border-danger",
          )}
          placeholder="you@curionex.com"
          {...register("email")}
        />
        {errors.email ? (
          <p className="text-xs text-danger" role="alert">
            {errors.email.message}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="password"
          className="text-sm font-medium text-foreground"
        >
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            className={cn(
              "h-10 w-full rounded-lg border border-border bg-background px-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground",
              errors.password && "border-danger",
            )}
            placeholder="••••••••"
            {...register("password")}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 inline-flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
            aria-label={showPassword ? "Hide password" : "Show password"}
            onClick={() => setShowPassword((value) => !value)}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
        {errors.password ? (
          <p className="text-xs text-danger" role="alert">
            {errors.password.message}
          </p>
        ) : null}
      </div>

      <Button type="submit" className="w-full" loading={isSubmitting}>
        Sign in
      </Button>
    </form>
  );
}
