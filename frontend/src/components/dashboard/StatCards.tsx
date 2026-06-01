import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/utils/cn";
import { Server, Monitor, AlertTriangle, Terminal } from "lucide-react";
import type { DashboardStats } from "@/types";
import type { LucideIcon } from "lucide-react";

interface StatCardsProps {
  stats?: DashboardStats;
  isLoading: boolean;
}

interface StatItem {
  label: string;
  value: number;
  icon: LucideIcon;
  color: string;
}

/** Summary stat cards for dashboard overview */
export function StatCards({ stats, isLoading }: StatCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Card key={i}>
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-16" />
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const items: StatItem[] = [
    { label: "Virtual Machines", value: stats.totalVMs, icon: Server, color: "text-info" },
    { label: "Physical Hosts", value: stats.totalHosts, icon: Monitor, color: "text-accent" },
    { label: "Active Alerts", value: stats.activeAlerts, icon: AlertTriangle, color: "text-warning" },
    { label: "Running Operations", value: stats.runningOperations, icon: Terminal, color: "text-success" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-secondary">{item.label}</span>
            <item.icon className={cn("h-4 w-4", item.color)} />
          </div>
          <p className="mt-2 text-2xl font-bold text-text-primary">{item.value}</p>
        </Card>
      ))}
    </div>
  );
}
