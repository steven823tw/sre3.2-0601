import type { Severity, AlertStatus } from "@/utils/constants";

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  status: AlertStatus;
  source: string;
  resource: string;
  resourceId: string;
  metric: string;
  value: string;
  threshold: string;
  triggeredAt: string;
  acknowledgedAt: string | null;
  resolvedAt: string | null;
  acknowledgedBy: string | null;
  tags: string[];
}

export interface AlertListParams {
  severity?: Severity;
  status?: AlertStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  counts: Record<Severity, number>;
  statusCounts: Record<AlertStatus, number>;
}
