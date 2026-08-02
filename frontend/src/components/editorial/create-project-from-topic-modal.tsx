"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  CategoryPicker,
  TagPicker,
} from "@/components/projects/taxonomy-pickers";
import { Button } from "@/components/ui/button";
import { Field, TextArea, TextInput } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import type { EditorialTopic } from "@/lib/editorial/types";
import { useCreateProjectFromTopic } from "@/lib/editorial/hooks";
import { useCategories, useTags } from "@/lib/projects/hooks";

const schema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().max(20000).optional(),
  category_id: z.string().nullable(),
  tag_ids: z.array(z.string()),
});

type FormValues = z.infer<typeof schema>;

type CreateProjectFromTopicModalProps = {
  open: boolean;
  topic: EditorialTopic | null;
  onClose: () => void;
  onCreated: (projectId: string) => void;
};

export function CreateProjectFromTopicModal({
  open,
  topic,
  onClose,
  onCreated,
}: CreateProjectFromTopicModalProps) {
  const { data: categories = [] } = useCategories(true);
  const { data: tags = [] } = useTags();
  const createFromTopic = useCreateProjectFromTopic();
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
      category_id: null,
      tag_ids: [],
    },
  });

  useEffect(() => {
    if (!open || !topic) return;
    reset({
      name: topic.title,
      description: topic.description ?? "",
      category_id: null,
      tag_ids: [],
    });
  }, [open, topic, reset]);

  async function onSubmit(values: FormValues) {
    if (!topic) return;
    try {
      const result = await createFromTopic.mutateAsync({
        topicId: topic.id,
        payload: {
          name: values.name,
          description: values.description || null,
          category_id: values.category_id,
          tag_ids: values.tag_ids,
        },
      });
      toast({ title: "Project created from topic", tone: "success" });
      onCreated(result.project.id);
      onClose();
    } catch (error) {
      toast({
        title:
          error instanceof ApiError
            ? error.detail
            : "Unable to create project",
        tone: "error",
      });
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create project from topic"
      description="Creates a Project and links it to this editorial topic. Does not create a Knowledge Pack."
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <Field label="Project name" htmlFor="topic-project-name" error={errors.name?.message}>
          <TextInput id="topic-project-name" {...register("name")} />
        </Field>
        <Field
          label="Description"
          htmlFor="topic-project-description"
          error={errors.description?.message}
        >
          <TextArea id="topic-project-description" rows={3} {...register("description")} />
        </Field>
        <Field label="Category" htmlFor="topic-project-category">
          <CategoryPicker
            categories={categories}
            value={watch("category_id")}
            onChange={(id) => setValue("category_id", id)}
          />
        </Field>
        <Field label="Tags" htmlFor="topic-project-tags">
          <TagPicker
            tags={tags}
            value={watch("tag_ids")}
            onChange={(ids) => setValue("tag_ids", ids)}
          />
        </Field>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting || createFromTopic.isPending}>
            Create project
          </Button>
        </div>
      </form>
    </Modal>
  );
}
