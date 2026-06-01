import { cn } from "@/utils/cn";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatRelativeTime } from "@/utils/formatTime";
import { CheckCircle, XCircle } from "lucide-react";
import type { Alert } from "@/types/alert";
import type { Severity } from "@/utils/constants";

interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (id: string) => void;
  onResolve: (id: string) => void;
}

const SEVERITY_CARD_STYLES: Record<Severity, string> = {
  P0: "border-l-2 border-l-red-500 bg-red-500/5 animate-pulse-alert",
  P1: "border-l-2 border-l-orange-500 bg-orange-500/5",
  P2: "border-l-2 border-l-yellow-500",
  P3: "border-l-2 border-l-blue-500",
  P4: "border-l-2 border-l-gray-500",
};

/** Alert card with severity indicator, status, and action buttons */
export function AlertCard({ alert, onAcknowledge, onResolve }: AlertCardProps) {
  const isActive = alert.status === "active";

  return (
    <div
      className={cn(
        "rounded-lg border bg-bg-secondary p-4 transition-colors hover:bg-bg-tertiary",
        isActive ? "border-border" : "border-border/50 opacity-70",
        SEVERITY_CARD_STYLES[alert.severity],
      )}
      role="article"
      aria-label={`${alert.severity} alert: ${alert.title}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge severity={alert.severity}>{alert.severity}</Badge>
            <h3 className="text-sm font-semibold text-text-primary truncate">{alert.title}</h3>
          </div>
          <p className="text-xs text-text-secondary mb-2 line-clamp-2">{alert.description}</p>
          <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">
            <span>Resource: <span className="font-medium text-text-primary">{alert.resource}</span></span>
            <span>Source: {alert.source}</span>
            <span>{formatRelativeTime(alert.triggeredAt)}</span>
            <Badge variant="outline">{alert.status}</Badge>
          </div>
        </div>
        {isActive && (
          <div className="flex shrink-0 gap-1.5">
            <Button size="sm" variant="secondary" onClick={() => onAcknowledge(alert.id)} aria-label={`Acknowledge alert ${alert.title}`}>
              <CheckCircle className="h-3.5 w-3.5" />
              Ack
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onResolve(alert.id)} aria-label={`Resolve alert ${alert.title}`}>
              <XCircle className="h-3.5 w-3.5" />
              Resolve
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
