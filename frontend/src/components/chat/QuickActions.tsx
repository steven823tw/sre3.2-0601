import { cn } from "@/utils/cn";
import { Server, Bell, HelpCircle, Stethoscope } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface QuickAction {
  label: string;
  message: string;
  icon: LucideIcon;
}

interface QuickActionsProps {
  onAction: (message: string) => void;
}

const actions: QuickAction[] = [
  { label: "View Clusters", message: "Show me the cluster overview", icon: Server },
  { label: "View Alerts", message: "Show me active alerts", icon: Bell },
  { label: "Help", message: "What can you help me with?", icon: HelpCircle },
  { label: "Diagnose web-01", message: "Diagnose web-prod-01 health issues", icon: Stethoscope },
];

/** Quick action chips for the chat welcome screen */
export function QuickActions({ onAction }: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Quick actions">
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={() => onAction(action.message)}
          className={cn(
            "inline-flex items-center gap-2 rounded-full border border-border bg-bg-tertiary px-4 py-2 text-sm text-text-secondary",
            "transition-colors hover:border-accent/50 hover:bg-bg-hover hover:text-text-primary",
          )}
          aria-label={action.label}
        >
          <action.icon className="h-4 w-4" />
          {action.label}
        </button>
      ))}
    </div>
  );
}
