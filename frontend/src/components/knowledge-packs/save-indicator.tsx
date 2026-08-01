"use client";

import { memo } from "react";

type SaveIndicatorProps = {
  saving: boolean;
  dirty: boolean;
  /** Relative label such as "just now" or "2 minutes ago" */
  savedLabel?: string | null;
};

export const SaveIndicator = memo(function SaveIndicator({
  saving,
  dirty,
  savedLabel,
}: SaveIndicatorProps) {
  let text = "Saved";
  if (saving) text = "Saving...";
  else if (dirty) text = "Unsaved changes";
  else if (savedLabel) text = `Saved ${savedLabel}`;

  return (
    <p
      className="text-sm text-muted-foreground"
      aria-live="polite"
      data-testid="save-status"
    >
      {text}
    </p>
  );
});
