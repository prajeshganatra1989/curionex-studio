"use client";

import { memo } from "react";

import {
  countWords,
  DEFAULT_NARRATION_WPM,
  formatNarrationEstimate,
} from "@/lib/scripts/metrics";

type NarrationEstimateProps = {
  text: string;
  wordsPerMinute?: number;
  className?: string;
};

export const NarrationEstimate = memo(function NarrationEstimate({
  text,
  wordsPerMinute = DEFAULT_NARRATION_WPM,
  className,
}: NarrationEstimateProps) {
  const words = countWords(text);
  return (
    <span className={className} data-testid="narration-estimate">
      {formatNarrationEstimate(words, wordsPerMinute)}
    </span>
  );
});
