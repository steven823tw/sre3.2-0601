import { useState, useCallback } from "react";

import { useAssets } from "@/hooks/useAssets";
import { useFilterStore } from "@/stores/filterStore";
import { Tabs } from "@/components/ui/Tabs";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { FilterBar } from "./FilterBar";
import { AssetTable } from "./AssetTable";
import { DetailPanel } from "./DetailPanel";
import { BatchActions } from "./BatchActions";
import { Server, AlertTriangle, RefreshCw } from "lucide-react";
import type { Asset } from "@/types/asset";
import type { AssetType } from "@/utils/constants";

const TYPE_TABS = [
  { id: "vm", label: "Virtual Machines" },
  { id: "physical", label: "Physical Hosts" },
  { id: "storage", label: "Storage" },
];

/** Resources page with asset list, filters, and detail panel */
export function ResourcesView() {
  const { assetType, assetPlatform, assetStatus, assetSearch, setAssetType } = useFilterStore();
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const { data, isLoading, error, refetch } = useAssets({
    type: assetType || undefined,
    platform: assetPlatform || undefined,
    status: assetStatus || undefined,
    search: assetSearch || undefined,
  });

  const assets = data?.items ?? [];

  const handleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleSelectAll = useCallback((ids: string[]) => {
    setSelectedIds(new Set(ids));
  }, []);

  const handleRowClick = useCallback((asset: Asset) => {
    setSelectedAsset(asset);
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-bg-secondary rounded-xl border border-border">
          <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Failed to load resources
          </h3>
          <p className="text-sm text-text-secondary mb-4">{error.message}</p>
          <Button variant="secondary" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Resources</h1>
      </div>

      {/* Type tabs */}
      <Tabs
        tabs={TYPE_TABS}
        activeTab={assetType || "vm"}
        onTabChange={(id) => setAssetType(id as AssetType)}
      />

      {/* Filter bar */}
      <FilterBar />

      {/* Batch actions */}
      <BatchActions
        selectedCount={selectedIds.size}
        onClearSelection={handleClearSelection}
        onMigrate={() => {}}
        onShutdown={() => {}}
        onBoot={() => {}}
        onDelete={() => {}}
      />

      {/* Asset table */}
      {assets.length > 0 || isLoading ? (
        <AssetTable
          assets={assets}
          isLoading={isLoading}
          selectedIds={selectedIds}
          onSelect={handleSelect}
          onSelectAll={handleSelectAll}
          onRowClick={handleRowClick}
        />
      ) : (
        <EmptyState
          icon={Server}
          title="No resources found"
          description="No assets match your current filters. Try adjusting your search criteria."
        />
      )}

      {/* Detail panel */}
      <DetailPanel
        asset={selectedAsset}
        isLoading={false}
        onClose={() => setSelectedAsset(null)}
      />
    </div>
  );
}
