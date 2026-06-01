import { useQuery } from "@tanstack/react-query";
import { getOperations, getOperationById } from "@/api/operations";
import type { OperationListParams } from "@/types/operation";

export function useOperations(params?: OperationListParams) {
  return useQuery({
    queryKey: ["operations", params],
    queryFn: () => getOperations(params),
  });
}

export function useOperation(id: string) {
  return useQuery({
    queryKey: ["operations", id],
    queryFn: () => getOperationById(id),
    enabled: !!id,
  });
}
