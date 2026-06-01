import { cn } from "@/utils/cn";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export function Button({ variant = "primary", size = "md", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" && "bg-accent text-bg-primary hover:bg-accent-hover",
        variant === "secondary" && "bg-bg-tertiary text-text-primary hover:bg-bg-hover border border-border",
        variant === "ghost" && "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
        variant === "danger" && "bg-danger/15 text-red-400 hover:bg-danger/25 border border-danger/30",
        size === "sm" && "h-7 px-2 text-xs gap-1",
        size === "md" && "h-9 px-3 text-sm gap-1.5",
        size === "lg" && "h-11 px-4 text-base gap-2",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
