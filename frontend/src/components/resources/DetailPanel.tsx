import { cn } from "@/utils/cn";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tabs } from "@/components/ui/Tabs";
import { X } from "lucide-react";
import { useState } from "react";
import { formatBytes } from "@/utils/formatBytes";
import { formatDateTime } from "@/utils/formatTime";
import type { Asset } from "@/types/asset";

interface DetailPanelProps {
  asset: Asset | null;
  isLoading: boolean;
  onClose: () => void;
}

const DETAIL_TABS = [
  { id: "overview", label: "Overview" },
  { id: "monitor", label: "Monitor" },
  { id: "snapshots", label: "Snapshots" },
  { id: "logs", label: "Logs" },
];

/** Right-side slide-in detail panel for selected asset */
export function DetailPanel({ asset, isLoading, onClose }: DetailPanelProps) {
  const [activeTab, setActiveTab] = useState("overview");

  if (!asset && !isLoading) return null;

  return (
    <div
      className={cn(
        "fixed right-0 top-0 z-40 h-full w-96 border-l border-border bg-bg-secondary shadow-2xl",
        "animate-slide-in-right",
      )}
      role="complementary"
      aria-label="Asset detail panel"
    >
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-border px-4">
        <h2 className="text-sm font-semibold text-text-primary truncate">
          {asset?.name ?? "Loading..."}
        </h2>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-text-secondary hover:text-text-primary hover:bg-bg-hover"
          aria-label="Close detail panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {isLoading || !asset ? (
        /* Rich skeleton loading state matching the Overview tab layout */
        <div className="p-4 space-y-6">
          {/* Status + platform skeleton */}
          <div className="flex items-center gap-3">
            <Skeleton className="h-5 w-5 rounded-full" />
            <div className="space-y-1.5">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>

          {/* Resource metric cards skeleton */}
          <div className="grid grid-cols-3 gap-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="rounded-lg border border-border bg-bg-tertiary p-3 text-center space-y-1.5"
              >
                <Skeleton className="mx-auto h-3 w-8" />
                <Skeleton className="mx-auto h-6 w-12" />
                <Skeleton className="mx-auto h-2.5 w-16" />
              </div>
            ))}
          </div>

          {/* Details rows skeleton */}
          <div className="space-y-3">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="flex justify-between">
                <Skeleton className="h-3.5 w-16" />
                <Skeleton className="h-3.5 w-28" />
              </div>
            ))}
          </div>

          {/* Tags skeleton */}
          <div className="flex gap-1.5">
            <Skeleton className="h-5 w-14 rounded-full" />
            <Skeleton className="h-5 w-18 rounded-full" />
            <Skeleton className="h-5 w-10 rounded-full" />
          </div>
        </div>
      ) : (
        <>
          {/* Tabs */}
          <Tabs tabs={DETAIL_TABS} activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Content */}
          <div className="overflow-y-auto p-4" style={{ height: "calc(100% - 7rem)" }}>
            {activeTab === "overview" && (
              <div className="space-y-4">
                {/* Status and platform */}
                <div className="flex items-center gap-3">
                  <StatusDot status={asset.status} size="lg" />
                  <div>
                    <p className="text-sm font-medium text-text-primary capitalize">{asset.status}</p>
                    <p className="text-xs text-text-secondary">{asset.platform} / {asset.os}</p>
                  </div>
                </div>

                {/* Resource metrics */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "CPU", metric: asset.cpu },
                    { label: "Memory", metric: asset.memory },
                    { label: "Storage", metric: asset.storage },
                  ].map(({ label, metric }) => (
                    <div key={label} className="rounded-lg border border-border bg-bg-tertiary p-3 text-center">
                      <p className="text-xs text-text-secondary">{label}</p>
                      <p className="mt-1 text-lg font-semibold text-text-primary">{metric.percent}%</p>
                      <p className="text-[10px] text-text-secondary">
                        {label === "Storage"
                          ? formatBytes(metric.used * 1024 * 1024 * 1024)
                          : `${metric.used}/${metric.total}`}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Details */}
                <div className="space-y-2">
                  {[
                    { label: "IP", value: asset.ip },
                    { label: "Cluster", value: asset.cluster },
                    { label: "Last Seen", value: formatDateTime(asset.lastSeen) },
                    { label: "Created", value: formatDateTime(asset.createdAt) },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span className="text-text-secondary">{label}</span>
                      <span className="font-mono text-text-primary">{value}</span>
                    </div>
                  ))}
                </div>

                {/* Tags */}
                {asset.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {asset.tags.map((tag) => (
                      <Badge key={tag} variant="outline">{tag}</Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "monitor" && (
              <p className="text-sm text-text-secondary">Monitoring data will be displayed here.</p>
            )}
            {activeTab === "snapshots" && (
              <p className="text-sm text-text-secondary">Snapshot history will be displayed here.</p>
            )}
            {activeTab === "logs" && (
              <p className="text-sm text-text-secondary">Recent logs will be displayed here.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
