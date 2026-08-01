import Image from "next/image";

import { cn } from "@/lib/utils";

type BrandMarkProps = {
  className?: string;
  size?: number;
  priority?: boolean;
};

/** Compact network “C” mark. */
export function BrandMark({ className, size = 40, priority }: BrandMarkProps) {
  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 overflow-hidden rounded-full bg-black",
        className,
      )}
      style={{ width: size, height: size }}
    >
      <Image
        src="/brand/curionex-mark.png"
        alt=""
        width={size}
        height={size}
        priority={priority}
        className="h-full w-full object-cover"
      />
    </span>
  );
}

type BrandLogoProps = {
  className?: string;
  priority?: boolean;
  /** `sidebar` = horizontal lockup; `hero` = larger login treatment */
  variant?: "sidebar" | "hero";
  showTagline?: boolean;
};

/**
 * Horizontal Curionex lockup matching the dashboard mockup:
 * mark + CURIONEX wordmark (+ optional tagline).
 *
 * The circular badge PNG (`curionex-logo.png`) is unsuitable for sidebar height;
 * we compose mark + typography instead so branding stays readable.
 */
export function BrandLogo({
  className,
  priority,
  variant = "sidebar",
  showTagline = true,
}: BrandLogoProps) {
  const isHero = variant === "hero";
  const markSize = isHero ? 72 : 44;

  return (
    <div
      className={cn(
        "flex items-center gap-3",
        isHero && "flex-col text-center gap-4",
        className,
      )}
      role="img"
      aria-label="Curionex"
    >
      <BrandMark size={markSize} priority={priority} className="glow-brand" />
      <div className={cn(isHero && "space-y-1")}>
        <p
          className={cn(
            "font-semibold tracking-[0.14em] text-foreground",
            isHero ? "text-3xl" : "text-lg leading-none",
          )}
        >
          CURIONE
          <span className="text-gradient">X</span>
        </p>
        {showTagline ? (
          <p
            className={cn(
              "font-medium tracking-[0.22em]",
              isHero ? "text-xs" : "mt-1.5 text-[9px] leading-none",
            )}
          >
            <span className="text-foreground">DISCOVER.</span>{" "}
            <span className="text-brand-yellow">LEARN.</span>{" "}
            <span className="text-brand-orange">GROW.</span>
          </p>
        ) : null}
      </div>
    </div>
  );
}
