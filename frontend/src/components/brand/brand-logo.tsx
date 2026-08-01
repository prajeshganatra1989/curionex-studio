import Image from "next/image";

import { cn } from "@/lib/utils";

type BrandLogoProps = {
  className?: string;
  priority?: boolean;
};

/** Full Curionex lockup for sidebar and login. Raster assets can be swapped for SVG later. */
export function BrandLogo({ className, priority }: BrandLogoProps) {
  return (
    <Image
      src="/brand/curionex-logo.png"
      alt="Curionex"
      width={160}
      height={160}
      priority={priority}
      className={cn("h-10 w-auto object-contain", className)}
    />
  );
}

type BrandMarkProps = {
  className?: string;
  size?: number;
};

/** Compact network “C” mark for collapsed/mobile states. */
export function BrandMark({ className, size = 32 }: BrandMarkProps) {
  return (
    <Image
      src="/brand/curionex-mark.png"
      alt="Curionex"
      width={size}
      height={size}
      className={cn("object-contain", className)}
    />
  );
}
