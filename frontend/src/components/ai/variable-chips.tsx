"use client";

import { X } from "lucide-react";

import { TextInput } from "@/components/ui/field";
import { cn } from "@/lib/utils";

type VariableChipsProps = {
  variables: string[];
  onChange: (variables: string[]) => void;
  errors?: string[];
  className?: string;
};

export function VariableChips({
  variables,
  onChange,
  errors,
  className,
}: VariableChipsProps) {
  function addVariable(raw: string) {
    const name = raw.trim().replace(/^\{\{|\}\}$/g, "");
    if (!name || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) return;
    if (variables.includes(name)) return;
    onChange([...variables, name].sort());
  }

  function removeVariable(name: string) {
    onChange(variables.filter((item) => item !== name));
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex flex-wrap gap-2" data-testid="variable-chips">
        {variables.map((variable) => (
          <span
            key={variable}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-surface-elevated px-2 py-1 text-xs font-medium text-foreground"
          >
            {`{{${variable}}}`}
            <button
              type="button"
              className="rounded p-0.5 text-muted-foreground hover:bg-surface-hover hover:text-foreground"
              aria-label={`Remove ${variable}`}
              onClick={() => removeVariable(variable)}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const form = event.currentTarget;
          const input = form.elements.namedItem("variable") as HTMLInputElement;
          addVariable(input.value);
          input.value = "";
        }}
      >
        <TextInput
          name="variable"
          placeholder="Add variable (e.g. topic)"
          aria-label="Add variable"
          className="max-w-xs"
        />
        <button
          type="submit"
          className="text-sm text-brand-orange hover:underline"
        >
          Add
        </button>
      </form>
      {errors?.length ? (
        <ul className="space-y-1" role="alert">
          {errors.map((error) => (
            <li key={error} className="text-xs text-danger">
              {error}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
