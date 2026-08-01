"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

type ToastTone = "success" | "error" | "info";

type ToastItem = {
  id: string;
  title: string;
  description?: string;
  tone: ToastTone;
};

type ToastContextValue = {
  toast: (input: {
    title: string;
    description?: string;
    tone?: ToastTone;
  }) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const toneClass: Record<ToastTone, string> = {
  success: "border-success/40 bg-success/10",
  error: "border-danger/40 bg-danger/10",
  info: "border-border bg-surface-elevated",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const toast = useCallback(
    (input: { title: string; description?: string; tone?: ToastTone }) => {
      const id = crypto.randomUUID();
      setItems((prev) => [
        ...prev,
        {
          id,
          title: input.title,
          description: input.description,
          tone: input.tone ?? "info",
        },
      ]);
      window.setTimeout(() => {
        setItems((prev) => prev.filter((item) => item.id !== id));
      }, 4200);
    },
    [],
  );

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-4 right-4 z-[80] flex w-[min(100%,22rem)] flex-col gap-2"
        aria-live="polite"
      >
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              "pointer-events-auto rounded-lg border px-3 py-2 shadow-[var(--shadow-panel)]",
              toneClass[item.tone],
            )}
            role="status"
          >
            <p className="text-sm font-medium text-foreground">{item.title}</p>
            {item.description ? (
              <p className="mt-0.5 text-xs text-muted-foreground">
                {item.description}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
