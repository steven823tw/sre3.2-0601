import { cn } from "@/utils/cn";

/**
 * Skeleton loading primitives for the SRE Platform.
 *
 * Provides composable placeholders for cards, tables, rows, and charts
 * so pages can render meaningful loading states while data is fetched.
 */

/* ------------------------------------------------------------------ */
/*  Base Skeleton                                                      */
/* ------------------------------------------------------------------ */

interface SkeletonProps {
  className?: string;
  /** Render multiple identical skeletons */
  count?: number;
}

/** Generic pulsing rectangle — building block for all other skeletons */
export function Skeleton({ className, count = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className={cn("animate-pulse rounded bg-bg-tertiary", className)}
          aria-hidden="true"
        />
      ))}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  SkeletonCard                                                       */
/* ------------------------------------------------------------------ */

interface SkeletonCardProps {
  className?: string;
}

/** Placeholder for dashboard metric / summary cards */
export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-bg-secondary p-4 space-y-3",
        className,
      )}
      aria-label="Loading card"
      role="status"
    >
      {/* Title bar */}
      <Skeleton className="h-4 w-3/4" />
      {/* Body lines */}
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  SkeletonTable                                                      */
/* ------------------------------------------------------------------ */

interface SkeletonTableProps {
  /** Number of data rows (excluding header) */
  rows?: number;
  /** Number of columns */
  cols?: number;
  className?: string;
}

/** Placeholder for resource / alert list tables */
export function SkeletonTable({ rows = 5, cols = 4, className }: SkeletonTableProps) {
  return (
    <div
      className={cn("space-y-2", className)}
      aria-label="Loading table"
      role="status"
    >
      {/* Header row — slightly thicker */}
      <div className="flex gap-4 px-1 py-2">
        {Array.from({ length: cols }, (_, j) => (
          <Skeleton
            key={`header-${j}`}
            className={cn("h-4", j === 0 ? "w-1/4" : "flex-1")}
          />
        ))}
      </div>

      {/* Data rows */}
      {Array.from({ length: rows }, (_, i) => (
        <SkeletonRow key={i} cols={cols} />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  SkeletonRow                                                        */
/* ------------------------------------------------------------------ */

interface SkeletonRowProps {
  /** Number of cells in the row */
  cols?: number;
  className?: string;
}

/** Single table row placeholder — first column narrower for name/ID fields */
export function SkeletonRow({ cols = 4, className }: SkeletonRowProps) {
  return (
    <div
      className={cn(
        "flex gap-4 rounded-md px-1 py-2 transition-colors",
        className,
      )}
      aria-hidden="true"
    >
      {Array.from({ length: cols }, (_, j) => (
        <Skeleton
          key={j}
          className={cn(
            "h-6",
            j === 0 ? "w-1/4" : "flex-1",
          )}
        />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  SkeletonChart                                                      */
/* ------------------------------------------------------------------ */

interface SkeletonChartProps {
  className?: string;
  /** Simulate a bar chart shape instead of a flat block */
  variant?: "area" | "bar";
}

/**
 * Placeholder for chart / visualisation areas.
 *
 * - `area` (default): mimics a line/area chart with a wavy inner shape.
 * - `bar`: mimics a bar chart with staggered column heights.
 */
export function SkeletonChart({ className, variant = "area" }: SkeletonChartProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-bg-secondary p-4",
        className,
      )}
      aria-label="Loading chart"
      role="status"
    >
      {/* Chart title placeholder */}
      <Skeleton className="mb-4 h-4 w-1/3" />

      {variant === "bar" ? (
        /* Bar chart: staggered columns */
        <div className="flex items-end gap-2 h-32">
          {[60, 80, 45, 90, 55, 70, 40, 85, 65, 75, 50, 60].map((h, i) => (
            <div
              key={i}
              className="flex-1 animate-pulse rounded-t bg-bg-tertiary"
              style={{ height: `${h}%` }}
              aria-hidden="true"
            />
          ))}
        </div>
      ) : (
        /* Area chart: filled block with inner wave silhouette */
        <div className="relative h-32 overflow-hidden rounded bg-bg-tertiary">
          <div
            className="absolute inset-x-0 bottom-0 h-3/4 animate-pulse rounded bg-bg-hover"
            aria-hidden="true"
          />
        </div>
      )}

      {/* X-axis labels placeholder */}
      <div className="mt-3 flex justify-between">
        <Skeleton className="h-3 w-8" />
        <Skeleton className="h-3 w-8" />
        <Skeleton className="h-3 w-8" />
      </div>
    </div>
  );
}
