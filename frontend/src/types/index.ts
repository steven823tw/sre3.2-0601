export type { Asset, AssetListParams, AssetListResponse, ResourceMetric } from "./asset";
export type { Alert, AlertListParams, AlertListResponse } from "./alert";
export type { Operation, OperationStep, OperationListParams, OperationListResponse } from "./operation";
export type { ChatMessage, ChatRequest, ChatResponse, Recommendation, OperationContext, MessageRole } from "./chat";

import type { Operation } from "./operation";

export interface DashboardStats {
  totalVMs: number;
  totalHosts: number;
  activeAlerts: number;
  runningOperations: number;
}

export interface AlertDistribution {
  severity: string;
  count: number;
}

export interface ResourceUsage {
  cluster: string;
  cpu: number;
  memory: number;
  storage: number;
}

export interface TrendDataPoint {
  date: string;
  alerts: number;
  operations: number;
  cpu: number;
  memory: number;
}

export interface DashboardData {
  stats: DashboardStats;
  alertDistribution: AlertDistribution[];
  resourceUsage: ResourceUsage[];
  trend: TrendDataPoint[];
  recentOperations: Operation[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
}
