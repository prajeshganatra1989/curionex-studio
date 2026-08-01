"use client";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";

type UnsavedChangesDialogProps = {
  open: boolean;
  saving?: boolean;
  onStay: () => void;
  onDiscard: () => void;
  onSaveAndContinue: () => void;
};

export function UnsavedChangesDialog({
  open,
  saving,
  onStay,
  onDiscard,
  onSaveAndContinue,
}: UnsavedChangesDialogProps) {
  return (
    <Modal
      open={open}
      onClose={onStay}
      title="Unsaved changes"
      description="You have edits that are not saved yet. What would you like to do?"
    >
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onStay}>
          Stay here
        </Button>
        <Button type="button" variant="secondary" onClick={onDiscard}>
          Discard changes
        </Button>
        <Button
          type="button"
          onClick={onSaveAndContinue}
          loading={saving}
          disabled={saving}
        >
          Save and continue
        </Button>
      </div>
    </Modal>
  );
}
