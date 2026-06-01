import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { TrendDataPoint } from "@/types";

interface TrendChartProps {
  data?: TrendDataPoint[];
  isLoading: boolean;
}

/**
 * 7-day CPU/Memory trend line chart.
 * Displays host-level CPU and Memory utilization over time.
 */
export function TrendChart({ data, isLoading }: TrendChartProps) {
  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-4 w-40 mb-4" />
        <Skeleton className="h-56 w-full" />
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-text-primary">
        7-Day Resource Trend
      </h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d36" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "#757575" }}
              tickFormatter={(val: string) => val.slice(5)}
              stroke="#2a2d36"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#757575" }}
              stroke="#2a2d36"
              domain={[0, 100]}
              tickFormatter={(val: number) => `${val}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1a1d24",
                border: "1px solid #2a2d36",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              labelStyle={{ color: "#e0e0e0" }}
              formatter={(value: number, name: string) => [
                `${value}%`,
                name === "cpu" ? "CPU" : "Memory",
              ]}
            />
            <Legend
              wrapperStyle={{ fontSize: "12px" }}
              formatter={(value: string) =>
                value === "cpu" ? "CPU" : "Memory"
              }
            />
            {/* CPU line — accent color */}
            <Line
              type="monotone"
              dataKey="cpu"
              stroke="#00BFA5"
              strokeWidth={2}
              dot={false}
              name="cpu"
            />
            {/* Memory line — info color */}
            <Line
              type="monotone"
              dataKey="memory"
              stroke="#448AFF"
              strokeWidth={2}
              dot={false}
              name="memory"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
