import { httpClient } from "./client";
import type { DashboardData } from "@/types";

export async function getDashboardData(): Promise<DashboardData> {
  return httpClient.get<DashboardData>("/dashboard");
}
