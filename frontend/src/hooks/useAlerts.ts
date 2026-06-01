import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAlerts, acknowledgeAlert, resolveAlert } from "@/api/alerts";
import type { AlertListParams } from "@/types/alert";

export function useAlerts(params?: AlertListParams) {
  return useQuery({
    queryKey: ["alerts", params],
    queryFn: () => getAlerts(params),
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => acknowledgeAlert(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => resolveAlert(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });
}
