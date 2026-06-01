import { cn } from "@/utils/cn";

interface StatusDotProps {
  status: "online" | "offline" | "warning" | "error" | "running" | "pending" | "completed" | "failed" | "cancelled";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const statusColors: Record<string, string> = {
  online: "bg-success",
  completed: "bg-success",
  offline: "bg-text-secondary",
  cancelled: "bg-text-secondary",
  warning: "bg-warning",
  pending: "bg-warning",
  error: "bg-danger",
  failed: "bg-danger",
  running: "bg-info",
};

export function StatusDot({ status, size = "md", className }: StatusDotProps) {
  return (
    <span
      className={cn(
        "inline-block rounded-full",
        size === "sm" && "h-2 w-2",
        size === "md" && "h-2.5 w-2.5",
        size === "lg" && "h-3 w-3",
        statusColors[status] ?? "bg-text-secondary",
        (status === "running" || status === "pending") && "animate-pulse",
        className
      )}
      aria-label={`Status: ${status}`}
    />
  );
}
