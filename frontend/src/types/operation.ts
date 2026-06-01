import type { RiskLevel, OperationStatus } from "@/utils/constants";

export interface OperationStep {
  id: string;
  label: string;
  status: OperationStatus;
  startedAt: string | null;
  completedAt: string | null;
  output: string | null;
  error: string | null;
}

export interface Operation {
  id: string;
  title: string;
  description: string;
  status: OperationStatus;
  risk: RiskLevel;
  target: string;
  targetId: string;
  command: string;
  steps: OperationStep[];
  currentStep: number;
  startedAt: string;
  completedAt: string | null;
  initiatedBy: string;
  duration: number | null;
  tags: string[];
}

export interface OperationListParams {
  status?: OperationStatus;
  risk?: RiskLevel;
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface OperationListResponse {
  items: Operation[];
  total: number;
}
