import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type ErrorStateProps = {
  title?: string;
  message: string;
  action?: ReactNode;
  className?: string;
};

export function ErrorState({
  title = "Something went wrong",
  message,
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm",
        className,
      )}
    >
      <p className="font-medium text-foreground">{title}</p>
      <p className="mt-1 text-muted-foreground">{message}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}
