"use client";

import { memo } from "react";

import { countWords } from "@/lib/knowledge-packs/metrics";

type WordCounterProps = {
  text: string;
  className?: string;
};

export const WordCounter = memo(function WordCounter({
  text,
  className,
}: WordCounterProps) {
  const words = countWords(text);
  return (
    <span className={className} data-testid="word-counter">
      {words.toLocaleString()} word{words === 1 ? "" : "s"}
    </span>
  );
});
