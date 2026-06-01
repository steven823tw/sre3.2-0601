import { useState, useCallback } from "react";
import { useAlerts, useAcknowledgeAlert, useResolveAlert } from "@/hooks/useAlerts";
import { useFilterStore } from "@/stores/filterStore";
import { cn } from "@/utils/cn";
import { Tabs } from "@/components/ui/Tabs";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { AlertCard } from "./AlertCard";
import { AlertFilters } from "./AlertFilters";
import { Bell, AlertTriangle, RefreshCw } from "lucide-react";
import { SEVERITY_LEVELS, SEVERITY_CONFIG } from "@/utils/constants";
import type { Severity } from "@/utils/constants";

/** Alerts page with severity tabs, filters, and alert cards */
export function AlertsView() {
  const [activeSeverity, setActiveSeverity] = useState<string>("all");
  const { alertStatus, alertSearch } = useFilterStore();

  const { data, isLoading, error, refetch } = useAlerts({
    severity: activeSeverity !== "all" ? (activeSeverity as Severity) : undefined,
    status: alertStatus || undefined,
    search: alertSearch || undefined,
  });

  const acknowledgeMutation = useAcknowledgeAlert();
  const resolveMutation = useResolveAlert();

  const handleAcknowledge = useCallback((id: string) => {
    acknowledgeMutation.mutate(id);
  }, [acknowledgeMutation]);

  const handleResolve = useCallback((id: string) => {
    resolveMutation.mutate(id);
  }, [resolveMutation]);

  const alerts = data?.items ?? [];
  const counts = data?.counts;
  const statusCounts = data?.statusCounts;
  const activeCount = statusCounts?.active ?? 0;

  const severityTabs = [
    { id: "all", label: "All", count: alerts.length },
    ...SEVERITY_LEVELS.map((s) => ({
      id: s,
      label: s,
      count: counts?.[s] ?? 0,
    })),
  ];

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-bg-secondary rounded-xl border border-border">
          <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Failed to load alerts
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
    <div className="space-y-4">
      {/* Header with severity counts */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Alerts</h1>
        <div className="flex items-center gap-3">
          {activeCount > 0 && (
            <div className="flex items-center gap-1.5 text-sm text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="font-medium">{activeCount} active</span>
            </div>
          )}
          {SEVERITY_LEVELS.map((severity) => {
            const count = counts?.[severity] ?? 0;
            if (count === 0) return null;
            const config = SEVERITY_CONFIG[severity];
            return (
              <div
                key={severity}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                  config.bg,
                  config.text,
                )}
              >
                <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
                {severity}: {count}
              </div>
            );
          })}
        </div>
      </div>

      {/* Severity tabs */}
      <Tabs tabs={severityTabs} activeTab={activeSeverity} onTabChange={setActiveSeverity} />

      {/* Filters */}
      <AlertFilters />

      {/* Alert list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }, (_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Bell}
          title="No alerts found"
          description="No alerts match your current filters. All systems are healthy."
        />
      )}
    </div>
  );
}
