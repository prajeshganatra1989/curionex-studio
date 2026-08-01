"use client";

import { memo } from "react";

import { countCharacters } from "@/lib/knowledge-packs/metrics";

type CharacterCounterProps = {
  text: string;
  className?: string;
};

export const CharacterCounter = memo(function CharacterCounter({
  text,
  className,
}: CharacterCounterProps) {
  const chars = countCharacters(text);
  return (
    <span className={className} data-testid="character-counter">
      {chars.toLocaleString()} character{chars === 1 ? "" : "s"}
    </span>
  );
});
