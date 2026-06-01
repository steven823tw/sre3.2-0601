import type { RiskLevel } from "@/utils/constants";

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  recommendations?: Recommendation[];
  operation?: OperationContext;
}

export interface Recommendation {
  step: number;
  title: string;
  description: string;
  action: string;
  params: Record<string, unknown>;
  risk_level: RiskLevel;
  estimated_time_ms: number;
}

export interface OperationContext {
  operationId: string;
  title: string;
  risk: RiskLevel;
  steps: string[];
  currentStep: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  confirmationRequired: boolean;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  sessionId: string;
}
