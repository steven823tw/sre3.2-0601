import { cn } from "@/utils/cn";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { formatDateTime, formatDuration } from "@/utils/formatTime";
import type { Operation } from "@/types/operation";

interface OperationDetailProps {
  operation: Operation | null;
  isOpen: boolean;
  onClose: () => void;
}

const STEP_STATUS_STYLES: Record<string, string> = {
  pending: "border-text-secondary text-text-secondary",
  running: "border-info text-info",
  completed: "border-success text-success",
  failed: "border-danger text-danger",
  cancelled: "border-text-secondary text-text-secondary",
};

/** Operation detail modal with step-by-step progress and timeline */
export function OperationDetail({ operation, isOpen, onClose }: OperationDetailProps) {
  if (!operation) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Operation Detail" size="lg">
      <div className="space-y-4">
        {/* Header info */}
        <div className="flex items-center gap-3">
          <StatusDot status={operation.status} size="lg" />
          <div>
            <h3 className="text-base font-semibold text-text-primary">{operation.title}</h3>
            <p className="text-xs text-text-secondary">{operation.description}</p>
          </div>
        </div>

        {/* Meta grid */}
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-bg-primary/50 p-3">
          {[
            { label: "Status", value: operation.status },
            { label: "Risk", value: operation.risk },
            { label: "Target", value: operation.target },
            { label: "Initiated By", value: operation.initiatedBy },
            { label: "Started", value: formatDateTime(operation.startedAt) },
            { label: "Duration", value: operation.duration ? formatDuration(operation.duration) : "In progress" },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-[10px] text-text-secondary uppercase tracking-wider">{label}</p>
              <p className="text-sm text-text-primary">{value}</p>
            </div>
          ))}
        </div>

        {/* Command */}
        <div className="rounded-lg border border-border bg-bg-primary/50 p-3">
          <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1">Command</p>
          <code className="text-xs text-accent break-all">{operation.command}</code>
        </div>

        {/* Steps timeline */}
        <div>
          <h4 className="mb-3 text-sm font-semibold text-text-primary">Steps</h4>
          <div className="space-y-3">
            {operation.steps.map((step, index) => (
              <div key={step.id} className="flex gap-3">
                {/* Timeline connector */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "flex h-6 w-6 items-center justify-center rounded-full border-2 text-xs font-medium",
                      STEP_STATUS_STYLES[step.status] ?? "border-text-secondary text-text-secondary",
                    )}
                  >
                    {index + 1}
                  </div>
                  {index < operation.steps.length - 1 && (
                    <div className="w-px flex-1 bg-border" />
                  )}
                </div>

                {/* Step content */}
                <div className="flex-1 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">{step.label}</span>
                    <Badge variant="outline">{step.status}</Badge>
                  </div>
                  {step.output && (
                    <p className="mt-1 text-xs text-success">{step.output}</p>
                  )}
                  {step.error && (
                    <p className="mt-1 text-xs text-danger">{step.error}</p>
                  )}
                  {step.startedAt && (
                    <p className="mt-1 text-[10px] text-text-secondary">
                      {formatDateTime(step.startedAt)}
                      {step.completedAt && ` - ${formatDateTime(step.completedAt)}`}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
