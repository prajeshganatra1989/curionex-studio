import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  loading?: boolean;
  children: ReactNode;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-gradient text-black font-semibold shadow-[var(--glow-brand)] hover:brightness-110 disabled:opacity-60",
  secondary:
    "border border-border bg-surface-elevated text-foreground hover:bg-surface-hover",
  ghost: "text-muted-foreground hover:bg-surface-hover hover:text-foreground",
};

export function Button({
  variant = "primary",
  loading,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm transition focus-visible:outline-none disabled:cursor-not-allowed",
        variants[variant],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "Please wait…" : children}
    </button>
  );
}
