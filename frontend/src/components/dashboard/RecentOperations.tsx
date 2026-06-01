import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatRelativeTime } from "@/utils/formatTime";
import { useNavigate } from "react-router-dom";
import type { Operation } from "@/types/operation";

interface RecentOperationsProps {
  operations?: Operation[];
  isLoading: boolean;
}

/** Recent operations list for the dashboard */
export function RecentOperations({ operations, isLoading }: RecentOperationsProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-4 w-40 mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-2.5 w-2.5 rounded-full" />
              <Skeleton className="h-3 flex-1" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-text-primary">Recent Operations</h3>
      {operations && operations.length > 0 ? (
        <div className="space-y-2">
          {operations.map((op) => (
            <button
              key={op.id}
              onClick={() => navigate("/operations")}
              className="flex w-full items-center gap-3 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-bg-hover"
              aria-label={`View operation: ${op.title}`}
            >
              <span className={`h-2 w-2 shrink-0 rounded-full ${op.status === "completed" ? "bg-success" : op.status === "failed" ? "bg-danger" : op.status === "running" ? "bg-info" : "bg-warning"}`} />
              <span className="flex-1 truncate text-sm text-text-primary">{op.title}</span>
              <span className="shrink-0 text-xs text-text-secondary">{formatRelativeTime(op.startedAt)}</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-sm text-text-secondary">No recent operations</p>
      )}
    </Card>
  );
}
