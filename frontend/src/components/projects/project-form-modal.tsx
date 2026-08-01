"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Field, TextArea, TextInput, TextSelect } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import {
  CategoryPicker,
  TagPicker,
} from "@/components/projects/taxonomy-pickers";
import { ApiError } from "@/lib/api/client";
import type { Project } from "@/lib/api/types";
import {
  useCategories,
  useCreateProject,
  useTags,
  useUpdateProject,
} from "@/lib/projects/hooks";
import { useToast } from "@/components/ui/toast";

const schema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().max(20000).optional(),
  status: z.enum(["draft", "active", "archived"]),
  category_id: z.string().nullable(),
  tag_ids: z.array(z.string()),
});

type FormValues = z.infer<typeof schema>;

type ProjectFormModalProps = {
  open: boolean;
  onClose: () => void;
  mode: "create" | "edit";
  project?: Project | null;
  onCreated?: (project: Project) => void;
};

export function ProjectFormModal({
  open,
  onClose,
  mode,
  project,
  onCreated,
}: ProjectFormModalProps) {
  const { data: categories = [] } = useCategories(true);
  const { data: tags = [] } = useTags();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject(project?.id ?? "");
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      description: "",
      status: "draft",
      category_id: null,
      tag_ids: [],
    },
  });

  useEffect(() => {
    if (!open) return;
    if (mode === "edit" && project) {
      reset({
        name: project.name,
        description: project.description ?? "",
        status: (project.status as FormValues["status"]) || "draft",
        category_id: project.category_id,
        tag_ids: project.tags.map((t) => t.id),
      });
    } else {
      reset({
        name: "",
        description: "",
        status: "draft",
        category_id: null,
        tag_ids: [],
      });
    }
  }, [open, mode, project, reset]);

  async function onSubmit(values: FormValues) {
    try {
      if (mode === "create") {
        const created = await createProject.mutateAsync({
          name: values.name,
          description: values.description || null,
          status: values.status === "archived" ? "draft" : values.status,
          category_id: values.category_id,
          tag_ids: values.tag_ids,
        });
        toast({ title: "Project created", tone: "success" });
        onClose();
        onCreated?.(created);
      } else if (project) {
        await updateProject.mutateAsync({
          name: values.name,
          description: values.description || null,
          status: values.status,
          category_id: values.category_id,
          tag_ids: values.tag_ids,
        });
        toast({ title: "Project updated", tone: "success" });
        onClose();
      }
    } catch (err) {
      toast({
        title: mode === "create" ? "Could not create project" : "Could not update project",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={mode === "create" ? "Create Project" : "Edit Project"}
      description={
        mode === "create"
          ? "Project codes are assigned automatically (CRX-####)."
          : "Project code cannot be changed."
      }
      size="lg"
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
        {mode === "edit" && project ? (
          <p className="rounded-lg border border-border bg-surface-elevated px-3 py-2 font-mono text-sm text-brand-amber">
            {project.project_code}
          </p>
        ) : null}

        <Field label="Name" htmlFor="name" error={errors.name?.message}>
          <TextInput id="name" {...register("name")} placeholder="Black Holes Explained" />
        </Field>

        <Field
          label="Description"
          htmlFor="description"
          error={errors.description?.message}
        >
          <TextArea
            id="description"
            {...register("description")}
            placeholder="What this project will teach"
          />
        </Field>

        <Field label="Status" htmlFor="status" error={errors.status?.message}>
          <TextSelect id="status" {...register("status")}>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            {mode === "edit" ? <option value="archived">Archived</option> : null}
          </TextSelect>
        </Field>

        <CategoryPicker
          categories={categories}
          value={watch("category_id")}
          onChange={(id) => setValue("category_id", id, { shouldValidate: true })}
        />

        <TagPicker
          tags={tags}
          value={watch("tag_ids")}
          onChange={(ids) => setValue("tag_ids", ids, { shouldValidate: true })}
        />

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting}>
            {mode === "create" ? "Create Project" : "Save changes"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
