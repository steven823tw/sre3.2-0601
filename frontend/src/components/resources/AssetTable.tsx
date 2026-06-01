import { useState, useCallback } from "react";
import { cn } from "@/utils/cn";
import { AssetRow } from "./AssetRow";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { ArrowUpDown } from "lucide-react";
import type { Asset } from "@/types/asset";

interface AssetTableProps {
  assets: Asset[];
  isLoading: boolean;
  selectedIds: Set<string>;
  onSelect: (id: string) => void;
  onSelectAll: (ids: string[]) => void;
  onRowClick: (asset: Asset) => void;
}

type SortField = "name" | "platform" | "status" | "cpu" | "memory";

/** Asset table with sortable columns and row selection */
export function AssetTable({ assets, isLoading, selectedIds, onSelect, onSelectAll, onRowClick }: AssetTableProps) {
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  }, [sortField]);

  const sorted = [...assets].sort((a, b) => {
    const order = sortOrder === "asc" ? 1 : -1;
    switch (sortField) {
      case "name": return a.name.localeCompare(b.name) * order;
      case "platform": return a.platform.localeCompare(b.platform) * order;
      case "status": return a.status.localeCompare(b.status) * order;
      case "cpu": return (a.cpu.percent - b.cpu.percent) * order;
      case "memory": return (a.memory.percent - b.memory.percent) * order;
      default: return 0;
    }
  });

  const allSelected = assets.length > 0 && assets.every((a) => selectedIds.has(a.id));

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      onSelectAll([]);
    } else {
      onSelectAll(assets.map((a) => a.id));
    }
  }, [allSelected, assets, onSelectAll]);

  if (isLoading) {
    return <SkeletonTable rows={8} cols={7} />;
  }

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <th
      className={cn("px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-secondary cursor-pointer select-none hover:text-text-primary")}
      onClick={() => handleSort(field)}
      aria-sort={sortField === field ? (sortOrder === "asc" ? "ascending" : "descending") : "none"}
    >
      <div className="flex items-center gap-1">
        {label}
        <ArrowUpDown className="h-3 w-3" />
      </div>
    </th>
  );

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full" role="grid">
        <thead className="bg-bg-tertiary">
          <tr>
            <th className="w-10 px-4 py-3">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={handleSelectAll}
                className="h-4 w-4 rounded border-border bg-bg-tertiary text-accent focus:ring-accent/50"
                aria-label="Select all assets"
              />
            </th>
            <SortHeader field="name" label="Name" />
            <SortHeader field="platform" label="Platform" />
            <SortHeader field="status" label="Status" />
            <SortHeader field="cpu" label="CPU" />
            <SortHeader field="memory" label="Memory" />
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-secondary">IP</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((asset) => (
            <AssetRow
              key={asset.id}
              asset={asset}
              isSelected={selectedIds.has(asset.id)}
              onSelect={onSelect}
              onClick={onRowClick}
            />
          ))}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div className="py-8 text-center text-sm text-text-secondary">No assets found</div>
      )}
    </div>
  );
}
