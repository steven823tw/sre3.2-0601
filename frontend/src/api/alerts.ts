import { httpClient } from "./client";
import type { Alert, AlertListParams, AlertListResponse } from "@/types/alert";

export async function getAlerts(params?: AlertListParams): Promise<AlertListResponse> {
  return httpClient.get<AlertListResponse>("/alerts", params as Record<string, string>);
}

export async function acknowledgeAlert(id: string): Promise<Alert> {
  return httpClient.patch<Alert>(`/alerts/${id}/acknowledge`);
}

export async function resolveAlert(id: string): Promise<Alert> {
  return httpClient.patch<Alert>(`/alerts/${id}/resolve`);
}
