import { cn, initials } from "@/lib/utils";

type AvatarInitialsProps = {
  name: string;
  className?: string;
};

export function AvatarInitials({ name, className }: AvatarInitialsProps) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface-elevated text-xs font-semibold text-foreground",
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}
