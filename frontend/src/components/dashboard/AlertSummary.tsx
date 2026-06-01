import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/utils/cn";
import { SEVERITY_CONFIG, ALERT_STATUSES } from "@/utils/constants";
import type { AlertDistribution } from "@/types";
import type { Severity, AlertStatus } from "@/utils/constants";

interface AlertSummaryProps {
  distribution?: AlertDistribution[];
  statusCounts?: Record<AlertStatus, number>;
  isLoading: boolean;
}

/** Alert distribution by severity and status */
export function AlertSummary({ distribution, statusCounts, isLoading }: AlertSummaryProps) {
  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-text-primary">Alert Summary</h3>

      {/* Severity distribution */}
      <div className="mb-4 space-y-2">
        {distribution?.map((item) => {
          const config = SEVERITY_CONFIG[item.severity as Severity];
          return (
            <div key={item.severity} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex h-2 w-2 rounded-full",
                    config?.dot ?? "bg-text-secondary",
                  )}
                />
                <span className="text-sm text-text-secondary">{item.severity}</span>
              </div>
              <span className={cn("text-sm font-medium", config?.text ?? "text-text-primary")}>
                {item.count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status counts */}
      <div className="border-t border-border pt-3">
        <h4 className="mb-2 text-xs font-medium text-text-secondary uppercase tracking-wider">By Status</h4>
        <div className="flex gap-4">
          {ALERT_STATUSES.map((status) => (
            <div key={status} className="text-center">
              <p className="text-lg font-semibold text-text-primary">{statusCounts?.[status] ?? 0}</p>
              <p className="text-xs text-text-secondary capitalize">{status}</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
