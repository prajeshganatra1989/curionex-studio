"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Field, TextArea, TextInput, TextSelect } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { ApiError } from "@/lib/api/client";
import type { KnowledgePackSummary } from "@/lib/api/types";
import {
  useCreateKnowledgePack,
  useCreateScript,
  useProjectKnowledgePacks,
} from "@/lib/projects/hooks";
import { useToast } from "@/components/ui/toast";

const packSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string().optional(),
  status: z.enum(["draft", "active", "archived"]),
});

type PackValues = z.infer<typeof packSchema>;

export function CreateKnowledgePackModal({
  open,
  onClose,
  projectId,
}: {
  open: boolean;
  onClose: () => void;
  projectId: string;
}) {
  const createPack = useCreateKnowledgePack(projectId);
  const { toast } = useToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PackValues>({
    resolver: zodResolver(packSchema),
    defaultValues: { name: "", description: "", status: "draft" },
  });

  async function onSubmit(values: PackValues) {
    try {
      await createPack.mutateAsync({
        name: values.name,
        description: values.description || null,
        status: values.status,
      });
      toast({ title: "Knowledge Pack created", tone: "success" });
      reset();
      onClose();
    } catch (err) {
      toast({
        title: "Could not create Knowledge Pack",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create Knowledge Pack"
      description="Section shells are created automatically. Editing comes in a later sprint."
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Field label="Name" htmlFor="pack-name" error={errors.name?.message}>
          <TextInput id="pack-name" {...register("name")} />
        </Field>
        <Field label="Description" htmlFor="pack-description">
          <TextArea id="pack-description" {...register("description")} />
        </Field>
        <Field label="Status" htmlFor="pack-status">
          <TextSelect id="pack-status" {...register("status")}>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
          </TextSelect>
        </Field>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting}>
            Create Knowledge Pack
          </Button>
        </div>
      </form>
    </Modal>
  );
}

const scriptSchema = z.object({
  title: z.string().trim().min(1, "Title is required"),
  description: z.string().optional(),
  knowledge_pack_id: z.string().nullable(),
});

type ScriptValues = z.infer<typeof scriptSchema>;

export function CreateScriptModal({
  open,
  onClose,
  projectId,
}: {
  open: boolean;
  onClose: () => void;
  projectId: string;
}) {
  const { data: packs } = useProjectKnowledgePacks(projectId);
  const createScript = useCreateScript(projectId);
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ScriptValues>({
    resolver: zodResolver(scriptSchema),
    defaultValues: {
      title: "",
      description: "",
      knowledge_pack_id: null,
    },
  });

  const packItems: KnowledgePackSummary[] = packs?.items ?? [];

  async function onSubmit(values: ScriptValues) {
    setSubmitting(true);
    try {
      await createScript.mutateAsync({
        title: values.title,
        description: values.description || null,
        knowledge_pack_id: values.knowledge_pack_id || null,
      });
      toast({ title: "Script created", tone: "success" });
      reset();
      onClose();
    } catch (err) {
      toast({
        title: "Could not create script",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create Script"
      description="Document shells and a content workflow are created automatically."
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Field label="Title" htmlFor="script-title" error={errors.title?.message}>
          <TextInput id="script-title" {...register("title")} />
        </Field>
        <Field label="Description" htmlFor="script-description">
          <TextArea id="script-description" {...register("description")} />
        </Field>
        <Field label="Knowledge Pack" htmlFor="script-pack">
          <TextSelect
            id="script-pack"
            {...register("knowledge_pack_id", {
              setValueAs: (v) => (v === "" ? null : v),
            })}
          >
            <option value="">None</option>
            {packItems.map((pack) => (
              <option key={pack.id} value={pack.id}>
                {pack.name}
              </option>
            ))}
          </TextSelect>
        </Field>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            Create Script
          </Button>
        </div>
      </form>
    </Modal>
  );
}
