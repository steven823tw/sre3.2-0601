import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { AlertDistribution as AlertDistributionType } from "@/types";

interface AlertDistributionProps {
  data?: AlertDistributionType[];
  isLoading: boolean;
}

/** Color map for alert severity levels */
const SEVERITY_COLORS: Record<string, string> = {
  P0: "#FF5252",
  P1: "#FF9800",
  P2: "#FFB300",
  P3: "#448AFF",
  P4: "#757575",
};

/** Human-readable labels for severity levels */
const SEVERITY_LABELS: Record<string, string> = {
  P0: "Critical",
  P1: "High",
  P2: "Medium",
  P3: "Low",
  P4: "Info",
};

/**
 * Alert severity distribution donut chart.
 * Shows the breakdown of alerts by severity level.
 */
export function AlertDistribution({ data, isLoading }: AlertDistributionProps) {
  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-4 w-40 mb-4" />
        <Skeleton className="h-48 w-full" />
      </Card>
    );
  }

  const total = data?.reduce((sum, item) => sum + item.count, 0) ?? 0;

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-text-primary">
        Alert Distribution
      </h3>

      <div className="flex items-center gap-6">
        {/* Donut chart */}
        <div className="h-48 w-48 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={72}
                dataKey="count"
                nameKey="severity"
                paddingAngle={2}
                strokeWidth={0}
              >
                {data?.map((entry) => (
                  <Cell
                    key={entry.severity}
                    fill={SEVERITY_COLORS[entry.severity] ?? "#757575"}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1d24",
                  border: "1px solid #2a2d36",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                labelStyle={{ color: "#e0e0e0" }}
                formatter={(value: number, _name: string, props: { payload?: { severity?: string } }) => [
                  `${value} alerts`,
                  SEVERITY_LABELS[props.payload?.severity ?? ""] ?? props.payload?.severity,
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend with counts */}
        <div className="flex-1 space-y-2">
          {data?.map((item) => {
            const color = SEVERITY_COLORS[item.severity] ?? "#757575";
            const label = SEVERITY_LABELS[item.severity] ?? item.severity;
            const percent = total > 0 ? ((item.count / total) * 100).toFixed(0) : "0";

            return (
              <div
                key={item.severity}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="inline-flex h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs text-text-secondary">
                    {item.severity} — {label}
                  </span>
                </div>
                <span className="text-xs font-medium text-text-primary">
                  {item.count}
                  <span className="ml-1 text-text-secondary">({percent}%)</span>
                </span>
              </div>
            );
          })}

          {/* Total */}
          <div className="border-t border-border pt-2 mt-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-text-secondary">
                Total
              </span>
              <span className="text-sm font-bold text-text-primary">
                {total}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
