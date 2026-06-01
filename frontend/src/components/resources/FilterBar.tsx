import { useFilterStore } from "@/stores/filterStore";
import { PLATFORMS } from "@/utils/constants";
import { Search, X } from "lucide-react";

/** Filter controls for the resources list */
export function FilterBar() {
  const {
    assetSearch, assetPlatform, assetStatus,
    setAssetSearch, setAssetPlatform, setAssetStatus,
    resetAssetFilters,
  } = useFilterStore();

  const hasFilters = assetSearch || assetPlatform || assetStatus;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          value={assetSearch}
          onChange={(e) => setAssetSearch(e.target.value)}
          placeholder="Search assets..."
          className="h-9 w-full rounded-lg border border-border bg-bg-tertiary pl-9 pr-3 text-sm text-text-primary placeholder:text-text-secondary focus:border-accent/50 focus:outline-none"
          aria-label="Search assets"
        />
      </div>

      <select
        value={assetPlatform}
        onChange={(e) => setAssetPlatform(e.target.value)}
        className="h-9 rounded-lg border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent/50 focus:outline-none"
        aria-label="Filter by platform"
      >
        <option value="">All Platforms</option>
        {PLATFORMS.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>

      <select
        value={assetStatus}
        onChange={(e) => setAssetStatus(e.target.value)}
        className="h-9 rounded-lg border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent/50 focus:outline-none"
        aria-label="Filter by status"
      >
        <option value="">All Statuses</option>
        <option value="online">Online</option>
        <option value="offline">Offline</option>
        <option value="warning">Warning</option>
        <option value="error">Error</option>
      </select>

      {hasFilters && (
        <button
          onClick={resetAssetFilters}
          className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-bg-tertiary px-3 text-sm text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Clear all filters"
        >
          <X className="h-3.5 w-3.5" />
          Clear
        </button>
      )}
    </div>
  );
}
