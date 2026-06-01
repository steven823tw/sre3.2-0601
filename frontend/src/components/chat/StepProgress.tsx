import { cn } from "@/utils/cn";
import type { OperationContext } from "@/types/chat";

interface StepProgressProps {
  operation: OperationContext;
}

const STATUS_ICONS: Record<string, string> = {
  pending: "○",
  running: "⟳",
  completed: "✓",
  failed: "✗",
  cancelled: "⊘",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "text-text-secondary",
  running: "text-info",
  completed: "text-success",
  failed: "text-danger",
  cancelled: "text-text-secondary",
};

/** Displays operation step progress with status icons */
export function StepProgress({ operation }: StepProgressProps) {
  const progress = operation.steps.length > 0
    ? Math.round((operation.currentStep / operation.steps.length) * 100)
    : 0;

  return (
    <div className="rounded-lg border border-border bg-bg-secondary p-4" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-text-primary">{operation.title}</h4>
        <span className="text-xs text-text-secondary">{progress}%</span>
      </div>
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-bg-tertiary">
        <div className="h-full rounded-full bg-accent transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>
      <div className="space-y-2">
        {operation.steps.map((stepLabel, index) => {
          const isCurrent = index === operation.currentStep;
          const isCompleted = index < operation.currentStep;
          const status = isCompleted ? "completed" : isCurrent ? operation.status : "pending";
          return (
            <div key={index} className={cn("flex items-center gap-3 rounded-md px-2 py-1.5 text-sm", isCurrent && "bg-accent/10")}>
              <span className={cn("w-4 text-center font-mono", STATUS_COLORS[status] ?? "text-text-secondary")}>
                {STATUS_ICONS[status] ?? "○"}
              </span>
              <span className={cn("flex-1", isCurrent ? "text-text-primary font-medium" : "text-text-secondary")}>
                {stepLabel}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
