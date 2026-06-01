import { useDashboard } from "@/hooks/useDashboard";
import { StatCards } from "./StatCards";
import { AlertSummary } from "./AlertSummary";
import { AlertDistribution } from "./AlertDistribution";
import { ResourceUsage } from "./ResourceUsage";
import { RecentOperations } from "./RecentOperations";
import { TrendChart } from "./TrendChart";
import { Button } from "@/components/ui/Button";
import { cn } from "@/utils/cn";
import { RefreshCw, AlertTriangle } from "lucide-react";

/**
 * Dashboard page with stat cards, resource usage bar chart,
 * alert distribution donut, alert summary, recent operations,
 * and 7-day CPU/Memory trend line chart.
 */
export function DashboardView() {
  const { data, isLoading, refetch, isFetching, error } = useDashboard();

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-bg-secondary rounded-xl border border-border">
          <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Failed to load dashboard
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Dashboard</h1>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          aria-label="Refresh dashboard"
        >
          <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Stat cards */}
      <StatCards stats={data?.stats} isLoading={isLoading} />

      {/* Resource usage bar chart */}
      <ResourceUsage data={data?.resourceUsage} isLoading={isLoading} />

      {/* Alert distribution donut + alert summary + recent operations */}
      <div className="grid gap-6 lg:grid-cols-2">
        <AlertDistribution
          data={data?.alertDistribution}
          isLoading={isLoading}
        />
        <RecentOperations operations={data?.recentOperations} isLoading={isLoading} />
      </div>

      {/* Alert summary by status */}
      <AlertSummary
        distribution={data?.alertDistribution}
        statusCounts={undefined}
        isLoading={isLoading}
      />

      {/* 7-day CPU/Memory trend */}
      <TrendChart data={data?.trend} isLoading={isLoading} />
    </div>
  );
}
