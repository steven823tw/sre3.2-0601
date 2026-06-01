import { useFilterStore } from "@/stores/filterStore";
import { ALERT_STATUSES } from "@/utils/constants";
import { Search, X } from "lucide-react";

/** Alert filter controls for status and search */
export function AlertFilters() {
  const {
    alertSearch, alertStatus,
    setAlertSearch, setAlertStatus,
    resetAlertFilters,
  } = useFilterStore();

  const hasFilters = alertSearch || alertStatus;

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          value={alertSearch}
          onChange={(e) => setAlertSearch(e.target.value)}
          placeholder="Search alerts..."
          className="h-9 w-full rounded-lg border border-border bg-bg-tertiary pl-9 pr-3 text-sm text-text-primary placeholder:text-text-secondary focus:border-accent/50 focus:outline-none"
          aria-label="Search alerts"
        />
      </div>

      {/* Status filter */}
      <select
        value={alertStatus}
        onChange={(e) => setAlertStatus(e.target.value as typeof alertStatus)}
        className="h-9 rounded-lg border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent/50 focus:outline-none"
        aria-label="Filter by status"
      >
        <option value="">All Statuses</option>
        {ALERT_STATUSES.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>

      {/* Clear */}
      {hasFilters && (
        <button
          onClick={resetAlertFilters}
          className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-bg-tertiary px-3 text-sm text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Clear filters"
        >
          <X className="h-3.5 w-3.5" />
          Clear
        </button>
      )}
    </div>
  );
}
