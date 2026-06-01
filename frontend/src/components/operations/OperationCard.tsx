import { cn } from "@/utils/cn";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatusDot } from "@/components/ui/StatusDot";
import { formatRelativeTime, formatDuration } from "@/utils/formatTime";
import { Eye, CheckCircle, XCircle } from "lucide-react";
import type { Operation } from "@/types/operation";
import type { RiskLevel } from "@/utils/constants";

interface OperationCardProps {
  operation: Operation;
  onViewDetail: (op: Operation) => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "bg-green-500/15 text-green-400",
  medium: "bg-yellow-500/15 text-yellow-400",
  high: "bg-orange-500/15 text-orange-400",
  critical: "bg-red-500/15 text-red-400",
};

/** Operation card with status, risk badge, and action buttons */
export function OperationCard({ operation, onViewDetail, onApprove, onReject }: OperationCardProps) {
  return (
    <div
      className="rounded-lg border border-border bg-bg-secondary p-4 transition-colors hover:bg-bg-tertiary"
      role="article"
      aria-label={`Operation: ${operation.title}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Title row */}
          <div className="flex items-center gap-2 mb-1">
            <StatusDot status={operation.status} />
            <h3 className="text-sm font-semibold text-text-primary truncate">{operation.title}</h3>
            <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", RISK_STYLES[operation.risk])}>
              {operation.risk}
            </span>
          </div>

          {/* Description */}
          <p className="text-xs text-text-secondary mb-2 line-clamp-2">{operation.description}</p>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">
            <span>Target: <span className="font-medium text-text-primary">{operation.target}</span></span>
            <span>By: {operation.initiatedBy}</span>
            <span>{formatRelativeTime(operation.startedAt)}</span>
            {operation.duration !== null && (
              <span>Duration: {formatDuration(operation.duration)}</span>
            )}
            <Badge variant="outline">{operation.status}</Badge>
          </div>
        </div>

        {/* Actions */}
        <div className="flex shrink-0 gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onViewDetail(operation)}
            aria-label={`View operation ${operation.title}`}
          >
            <Eye className="h-3.5 w-3.5" />
          </Button>
          {operation.status === "pending" && onApprove && onReject && (
            <>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onApprove(operation.id)}
                aria-label={`Approve operation ${operation.title}`}
              >
                <CheckCircle className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={() => onReject(operation.id)}
                aria-label={`Reject operation ${operation.title}`}
              >
                <XCircle className="h-3.5 w-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
