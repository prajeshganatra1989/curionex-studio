"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Field, TextInput } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import {
  useProductionSettings,
  useUpdateProductionSettings,
} from "@/lib/production/hooks";

const schema = z.object({
  approved_script_target: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .int()
    .min(1, "Must be at least 1")
    .max(10000, "Must be at most 10000"),
  daily_approved_script_target: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .int()
    .min(1, "Must be at least 1")
    .max(100, "Must be at most 100"),
  weekly_approved_script_target: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .int()
    .min(1, "Must be at least 1")
    .max(700, "Must be at most 700"),
});

type FormValues = z.infer<typeof schema>;

type ProductionSettingsDialogProps = {
  open: boolean;
  onClose: () => void;
};

export function ProductionSettingsDialog({
  open,
  onClose,
}: ProductionSettingsDialogProps) {
  const { data, isLoading, isError, error } = useProductionSettings(open);
  const updateSettings = useUpdateProductionSettings();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      approved_script_target: 120,
      daily_approved_script_target: 2,
      weekly_approved_script_target: 14,
    },
  });

  useEffect(() => {
    if (!open || !data) return;
    reset({
      approved_script_target: data.approved_script_target,
      daily_approved_script_target: data.daily_approved_script_target,
      weekly_approved_script_target: data.weekly_approved_script_target,
    });
  }, [open, data, reset]);

  async function onSubmit(values: FormValues) {
    try {
      await updateSettings.mutateAsync(values);
      toast({ title: "Production settings saved", tone: "success" });
      onClose();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.detail
          : "Unable to update production settings.";
      toast({ title: message, tone: "error" });
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Production settings"
      description="Tune approved-script targets for the 120-script journey."
    >
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading settings…</p>
      ) : null}

      {isError ? (
        <p className="text-sm text-danger" role="alert">
          {error instanceof ApiError
            ? error.detail
            : "Unable to load settings."}
        </p>
      ) : null}

      {!isLoading && !isError ? (
        <form
          className="space-y-4"
          onSubmit={(event) => void handleSubmit(onSubmit)(event)}
          data-testid="production-settings-form"
        >
          <Field
            label="Approved script target"
            htmlFor="approved_script_target"
            error={errors.approved_script_target?.message}
            hint="Overall goal (default 120)"
          >
            <TextInput
              id="approved_script_target"
              type="number"
              min={1}
              max={10000}
              {...register("approved_script_target")}
            />
          </Field>
          <Field
            label="Daily approved target"
            htmlFor="daily_approved_script_target"
            error={errors.daily_approved_script_target?.message}
          >
            <TextInput
              id="daily_approved_script_target"
              type="number"
              min={1}
              max={100}
              {...register("daily_approved_script_target")}
            />
          </Field>
          <Field
            label="Weekly approved target"
            htmlFor="weekly_approved_script_target"
            error={errors.weekly_approved_script_target?.message}
          >
            <TextInput
              id="weekly_approved_script_target"
              type="number"
              min={1}
              max={700}
              {...register("weekly_approved_script_target")}
            />
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting || updateSettings.isPending}>
              Save
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  );
}
