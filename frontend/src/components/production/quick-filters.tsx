"use client";

import { useMemo, useState } from "react";
import { Filter, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, TextInput, TextSelect } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { useCategories, useTags } from "@/lib/projects/hooks";
import {
  PRODUCTION_STAGES,
  PRODUCTION_STAGE_LABELS,
  QUALITY_BANDS,
  QUALITY_BAND_LABELS,
  type ProductionStage,
} from "@/lib/production/types";
import { cn } from "@/lib/utils";

export type ProductionFilterState = {
  search: string;
  production_stage: string;
  project_id: string;
  category_id: string;
  tag_id: string;
  quality_band: string;
  ai_job_status: string;
  stale_quality: boolean;
  blocked_only: boolean;
  pending_approval: boolean;
  sort: string;
};

export const DEFAULT_FILTERS: ProductionFilterState = {
  search: "",
  production_stage: "",
  project_id: "",
  category_id: "",
  tag_id: "",
  quality_band: "",
  ai_job_status: "",
  stale_quality: false,
  blocked_only: false,
  pending_approval: false,
  sort: "priority",
};

type QuickFiltersProps = {
  filters: ProductionFilterState;
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  onChange: (next: Partial<ProductionFilterState>) => void;
  onReset: () => void;
};

export function QuickFilters({
  filters,
  searchInput,
  onSearchInputChange,
  onChange,
  onReset,
}: QuickFiltersProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const activeCount = useMemo(() => {
    let count = 0;
    if (filters.production_stage) count += 1;
    if (filters.project_id) count += 1;
    if (filters.category_id) count += 1;
    if (filters.tag_id) count += 1;
    if (filters.quality_band) count += 1;
    if (filters.ai_job_status) count += 1;
    if (filters.stale_quality) count += 1;
    if (filters.blocked_only) count += 1;
    if (filters.pending_approval) count += 1;
    if (filters.search.trim()) count += 1;
    if (filters.sort && filters.sort !== "priority") count += 1;
    return count;
  }, [filters]);

  return (
    <div className="space-y-3" data-testid="quick-filters">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <TextInput
            value={searchInput}
            onChange={(event) => onSearchInputChange(event.target.value)}
            placeholder="Search projects or scripts…"
            className="pl-9"
            aria-label="Search production queue"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chip
            active={filters.pending_approval}
            onClick={() =>
              onChange({ pending_approval: !filters.pending_approval })
            }
          >
            Pending approval
          </Chip>
          <Chip
            active={filters.blocked_only}
            onClick={() => onChange({ blocked_only: !filters.blocked_only })}
          >
            Blocked
          </Chip>
          <Chip
            active={filters.production_stage === "needs_revision"}
            onClick={() =>
              onChange({
                production_stage:
                  filters.production_stage === "needs_revision"
                    ? ""
                    : "needs_revision",
              })
            }
          >
            Needs revision
          </Chip>
          <Chip
            active={filters.stale_quality}
            onClick={() => onChange({ stale_quality: !filters.stale_quality })}
          >
            Stale quality
          </Chip>
          <Button
            type="button"
            variant="secondary"
            className="h-9 px-3"
            onClick={() => setAdvancedOpen(true)}
            data-testid="open-advanced-filters"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
            {activeCount > 0 ? (
              <span className="rounded-md bg-brand-orange/15 px-1.5 text-[10px] tabular-nums text-brand-amber">
                {activeCount}
              </span>
            ) : null}
          </Button>
          {activeCount > 0 ? (
            <Button
              type="button"
              variant="ghost"
              className="h-9 px-3"
              onClick={onReset}
              aria-label="Reset filters"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </Button>
          ) : null}
        </div>
      </div>

      <AdvancedFilterDrawer
        open={advancedOpen}
        onClose={() => setAdvancedOpen(false)}
        filters={filters}
        onChange={onChange}
        onReset={onReset}
      />
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition",
        active
          ? "border-brand-orange/40 bg-brand-orange/10 text-brand-amber"
          : "border-border bg-surface-elevated text-muted-foreground hover:bg-surface-hover hover:text-foreground",
      )}
    >
      <Filter className="h-3.5 w-3.5" aria-hidden />
      {children}
    </button>
  );
}

type AdvancedFilterDrawerProps = {
  open: boolean;
  onClose: () => void;
  filters: ProductionFilterState;
  onChange: (next: Partial<ProductionFilterState>) => void;
  onReset: () => void;
};

export function AdvancedFilterDrawer({
  open,
  onClose,
  filters,
  onChange,
  onReset,
}: AdvancedFilterDrawerProps) {
  const { data: categories = [] } = useCategories(true);
  const { data: tags = [] } = useTags();

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Advanced filters"
      description="Narrow the production queue by stage, taxonomy, quality, and AI status."
      size="lg"
    >
      <div className="grid gap-4 sm:grid-cols-2" data-testid="advanced-filters">
        <Field label="Stage" htmlFor="prod-stage">
          <TextSelect
            id="prod-stage"
            value={filters.production_stage}
            onChange={(event) =>
              onChange({ production_stage: event.target.value })
            }
          >
            <option value="">All stages</option>
            {PRODUCTION_STAGES.map((stage) => (
              <option key={stage} value={stage}>
                {PRODUCTION_STAGE_LABELS[stage as ProductionStage]}
              </option>
            ))}
          </TextSelect>
        </Field>

        <Field label="Quality band" htmlFor="prod-quality-band">
          <TextSelect
            id="prod-quality-band"
            value={filters.quality_band}
            onChange={(event) =>
              onChange({ quality_band: event.target.value })
            }
          >
            <option value="">Any band</option>
            {QUALITY_BANDS.map((band) => (
              <option key={band} value={band}>
                {QUALITY_BAND_LABELS[band]}
              </option>
            ))}
          </TextSelect>
        </Field>

        <Field label="AI job status" htmlFor="prod-ai-status">
          <TextSelect
            id="prod-ai-status"
            value={filters.ai_job_status}
            onChange={(event) =>
              onChange({ ai_job_status: event.target.value })
            }
          >
            <option value="">Any status</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </TextSelect>
        </Field>

        <Field label="Sort" htmlFor="prod-sort">
          <TextSelect
            id="prod-sort"
            value={filters.sort}
            onChange={(event) => onChange({ sort: event.target.value })}
          >
            <option value="priority">Priority</option>
            <option value="updated_at">Recently updated</option>
            <option value="stage">Stage</option>
          </TextSelect>
        </Field>

        <Field label="Category" htmlFor="prod-category">
          <TextSelect
            id="prod-category"
            value={filters.category_id}
            onChange={(event) =>
              onChange({ category_id: event.target.value })
            }
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </TextSelect>
        </Field>

        <Field label="Tag" htmlFor="prod-tag">
          <TextSelect
            id="prod-tag"
            value={filters.tag_id}
            onChange={(event) => onChange({ tag_id: event.target.value })}
          >
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </TextSelect>
        </Field>

        <Field label="Project ID" htmlFor="prod-project-id" hint="Optional UUID">
          <TextInput
            id="prod-project-id"
            value={filters.project_id}
            onChange={(event) => onChange({ project_id: event.target.value })}
            placeholder="Filter by project id"
          />
        </Field>
      </div>

      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onReset}>
          <RotateCcw className="h-4 w-4" />
          Reset
        </Button>
        <Button type="button" variant="primary" onClick={onClose}>
          <X className="h-4 w-4" />
          Done
        </Button>
      </div>
    </Modal>
  );
}
