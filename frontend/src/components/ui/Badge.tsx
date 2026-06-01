import { cn } from "@/utils/cn";
import type { Severity } from "@/utils/constants";
import { SEVERITY_CONFIG } from "@/utils/constants";

interface BadgeProps {
  children: React.ReactNode;
  severity?: Severity;
  variant?: "default" | "outline" | "solid";
  className?: string;
}

export function Badge({ children, severity, variant = "default", className }: BadgeProps) {
  const config = severity ? SEVERITY_CONFIG[severity] : null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        variant === "outline" && "border",
        config ? cn(config.bg, config.text, variant === "outline" && config.border) : "bg-bg-tertiary text-text-secondary",
        severity === "P0" && "animate-pulse",
        className
      )}
    >
      {children}
    </span>
  );
}
