import { useState, useCallback } from "react";
import { useOperations } from "@/hooks/useOperations";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { httpClient } from "@/api/client";
import { Tabs } from "@/components/ui/Tabs";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { OperationCard } from "./OperationCard";
import { OperationDetail } from "./OperationDetail";
import { Terminal, AlertTriangle, RefreshCw } from "lucide-react";
import { OPERATION_STATUSES } from "@/utils/constants";
import type { Operation } from "@/types/operation";
import type { OperationStatus } from "@/utils/constants";

const statusTabs = [
  { id: "all", label: "All" },
  ...OPERATION_STATUSES.map((s) => ({ id: s, label: s.charAt(0).toUpperCase() + s.slice(1) })),
];

/** Operations page with status tabs and operation cards */
export function OperationsView() {
  const [activeStatus, setActiveStatus] = useState("all");
  const [detailOp, setDetailOp] = useState<Operation | null>(null);

  const { data, isLoading, error, refetch } = useOperations({
    status: activeStatus !== "all" ? (activeStatus as OperationStatus) : undefined,
  });

  const operations = data?.items ?? [];

  const queryClient = useQueryClient();
  const approveMutation = useMutation({
    mutationFn: (id: string) => httpClient.put('/operations/' + id + '/approve', {}),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["operations"] }),
  });
  const rejectMutation = useMutation({
    mutationFn: (id: string) => httpClient.put('/operations/' + id + '/reject', { reason: 'Rejected by operator' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["operations"] }),
  });

  const handleViewDetail = useCallback((op: Operation) => {
    setDetailOp(op);
  }, []);

  const handleApprove = useCallback((id: string) => {
    approveMutation.mutate(id);
  }, [approveMutation]);

  const handleReject = useCallback((id: string) => {
    rejectMutation.mutate(id);
  }, [rejectMutation]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-bg-secondary rounded-xl border border-border">
          <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Failed to load operations
          </h3>
          <p className="text-sm text-text-secondary mb-4">{error.message}</p>
          <Button variant="secondary" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">Operations</h1>
      </div>

      {/* Status tabs */}
      <Tabs tabs={statusTabs} activeTab={activeStatus} onTabChange={setActiveStatus} />

      {/* Operation list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }, (_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : operations.length > 0 ? (
        <div className="space-y-3">
          {operations.map((op) => (
            <OperationCard
              key={op.id}
              operation={op}
              onViewDetail={handleViewDetail}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Terminal}
          title="No operations found"
          description="No operations match the current filter."
        />
      )}

      {/* Detail modal */}
      <OperationDetail
        operation={detailOp}
        isOpen={detailOp !== null}
        onClose={() => setDetailOp(null)}
      />
    </div>
  );
}
