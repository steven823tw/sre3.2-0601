import { httpClient } from "./client";
import type { Operation, OperationListParams, OperationListResponse } from "@/types/operation";

export async function getOperations(params?: OperationListParams): Promise<OperationListResponse> {
  return httpClient.get<OperationListResponse>("/operations", params as Record<string, string>);
}

export async function getOperationById(id: string): Promise<Operation> {
  return httpClient.get<Operation>(`/operations/${id}`);
}
