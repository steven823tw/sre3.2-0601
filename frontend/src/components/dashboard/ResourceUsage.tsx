import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ResourceUsage as ResourceUsageType } from "@/types";

interface ResourceUsageProps {
  data?: ResourceUsageType[];
  isLoading: boolean;
}

/**
 * Cluster resource usage bar chart.
 * Displays CPU, Memory, and Storage utilization per cluster as grouped bars.
 */
export function ResourceUsage({ data, isLoading }: ResourceUsageProps) {
  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-56 w-full" />
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-text-primary">
        Cluster Resource Usage
      </h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d36" />
            <XAxis
              dataKey="cluster"
              tick={{ fontSize: 11, fill: "#757575" }}
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
              formatter={(value: number) => [`${value}%`]}
            />
            <Legend wrapperStyle={{ fontSize: "12px" }} />
            {/* CPU bars — accent color */}
            <Bar
              dataKey="cpu"
              fill="#00BFA5"
              radius={[3, 3, 0, 0]}
              name="CPU"
            />
            {/* Memory bars — info color */}
            <Bar
              dataKey="memory"
              fill="#448AFF"
              radius={[3, 3, 0, 0]}
              name="Memory"
            />
            {/* Storage bars — warning color */}
            <Bar
              dataKey="storage"
              fill="#FFB300"
              radius={[3, 3, 0, 0]}
              name="Storage"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
