import { cn } from "@/lib/utils";

type LoadingSkeletonProps = {
  className?: string;
};

export function LoadingSkeleton({ className }: LoadingSkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-surface-hover/80",
        className,
      )}
      aria-hidden
    />
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading dashboard">
      <LoadingSkeleton className="h-16 w-2/3" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <LoadingSkeleton key={i} className="h-28" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <LoadingSkeleton className="h-64" />
        <LoadingSkeleton className="h-64" />
      </div>
    </div>
  );
}
