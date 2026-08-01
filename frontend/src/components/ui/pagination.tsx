"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-muted-foreground">
        Showing{" "}
        <span className="tabular-nums text-foreground">
          {from}–{to}
        </span>{" "}
        of <span className="tabular-nums text-foreground">{total}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          className="h-9 px-3"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
          Prev
        </Button>
        <span className="min-w-20 text-center text-sm tabular-nums text-muted-foreground">
          {page} / {totalPages}
        </span>
        <Button
          type="button"
          variant="secondary"
          className="h-9 px-3"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
