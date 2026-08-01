"use client";

import { useMemo, useState } from "react";
import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, TextInput } from "@/components/ui/field";
import { useCreateCategory, useCreateTag } from "@/lib/projects/hooks";
import type { Category, Tag } from "@/lib/api/types";
import { ApiError } from "@/lib/api/client";
import { useToast } from "@/components/ui/toast";

type CategoryPickerProps = {
  categories: Category[];
  value: string | null;
  onChange: (id: string | null) => void;
  error?: string;
};

export function CategoryPicker({
  categories,
  value,
  onChange,
  error,
}: CategoryPickerProps) {
  const [query, setQuery] = useState("");
  const [creating, setCreating] = useState(false);
  const createCategory = useCreateCategory();
  const { toast } = useToast();

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return categories;
    return categories.filter((c) => c.name.toLowerCase().includes(q));
  }, [categories, query]);

  async function handleCreate() {
    const name = query.trim();
    if (!name) return;
    setCreating(true);
    try {
      const created = await createCategory.mutateAsync({ name });
      onChange(created.id);
      setQuery("");
      toast({ title: "Category created", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not create category",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    } finally {
      setCreating(false);
    }
  }

  return (
    <Field label="Category" htmlFor="category-search" error={error}>
      <TextInput
        id="category-search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search or create a category"
        list="category-options"
      />
      <datalist id="category-options">
        {filtered.map((c) => (
          <option key={c.id} value={c.name} />
        ))}
      </datalist>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          type="button"
          className={`rounded-md border px-2 py-1 text-xs ${
            value === null
              ? "border-brand-orange/50 bg-brand-orange/10 text-foreground"
              : "border-border text-muted-foreground"
          }`}
          onClick={() => onChange(null)}
        >
          None
        </button>
        {filtered.slice(0, 8).map((c) => (
          <button
            key={c.id}
            type="button"
            className={`rounded-md border px-2 py-1 text-xs ${
              value === c.id
                ? "border-brand-orange/50 bg-brand-orange/10 text-foreground"
                : "border-border text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => onChange(c.id)}
          >
            {c.name}
          </button>
        ))}
        {query.trim() &&
        !categories.some(
          (c) => c.name.toLowerCase() === query.trim().toLowerCase(),
        ) ? (
          <Button
            type="button"
            variant="secondary"
            className="h-7 px-2 text-xs"
            loading={creating}
            onClick={() => void handleCreate()}
          >
            <Plus className="h-3 w-3" />
            Create “{query.trim()}”
          </Button>
        ) : null}
      </div>
    </Field>
  );
}

type TagPickerProps = {
  tags: Tag[];
  value: string[];
  onChange: (ids: string[]) => void;
  error?: string;
};

export function TagPicker({ tags, value, onChange, error }: TagPickerProps) {
  const [query, setQuery] = useState("");
  const [creating, setCreating] = useState(false);
  const createTag = useCreateTag();
  const { toast } = useToast();

  const selected = tags.filter((t) => value.includes(t.id));
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const available = tags.filter((t) => !value.includes(t.id));
    if (!q) return available.slice(0, 10);
    return available.filter((t) => t.name.toLowerCase().includes(q)).slice(0, 10);
  }, [tags, value, query]);

  function toggle(id: string) {
    if (value.includes(id)) {
      onChange(value.filter((v) => v !== id));
    } else {
      onChange([...value, id]);
    }
  }

  async function handleCreate() {
    const name = query.trim();
    if (!name) return;
    setCreating(true);
    try {
      const created = await createTag.mutateAsync({ name });
      onChange([...value, created.id]);
      setQuery("");
      toast({ title: "Tag created", tone: "success" });
    } catch (err) {
      toast({
        title: "Could not create tag",
        description: err instanceof ApiError ? err.detail : "Try again.",
        tone: "error",
      });
    } finally {
      setCreating(false);
    }
  }

  return (
    <Field label="Tags" htmlFor="tag-search" error={error}>
      <div className="mb-2 flex flex-wrap gap-1.5">
        {selected.map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-surface-elevated px-2 py-0.5 text-xs text-foreground"
          >
            {tag.name}
            <button
              type="button"
              aria-label={`Remove ${tag.name}`}
              className="text-muted-foreground hover:text-foreground"
              onClick={() => toggle(tag.id)}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
      <TextInput
        id="tag-search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search or create tags"
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            const match = filtered[0];
            if (match) toggle(match.id);
          }
        }}
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {filtered.map((tag) => (
          <button
            key={tag.id}
            type="button"
            className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:border-brand-orange/40 hover:text-foreground"
            onClick={() => toggle(tag.id)}
          >
            {tag.name}
          </button>
        ))}
        {query.trim() &&
        !tags.some((t) => t.name.toLowerCase() === query.trim().toLowerCase()) ? (
          <Button
            type="button"
            variant="secondary"
            className="h-7 px-2 text-xs"
            loading={creating}
            onClick={() => void handleCreate()}
          >
            <Plus className="h-3 w-3" />
            Create “{query.trim()}”
          </Button>
        ) : null}
      </div>
    </Field>
  );
}
