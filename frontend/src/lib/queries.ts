import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/platforms';
import type { PlatformConfig } from '../types/platform';

/**
 * Query key factory for consistent cache management
 */
export const queryKeys = {
  platforms: ['platforms'] as const,
  platform: (id: string) => ['platforms', id] as const,
  devices: (platformId?: string, type?: string) =>
    ['devices', { platformId, type }] as const,
  vms: ['devices', { type: 'vm' }] as const,
  migrationHistory: ['migrations', 'history'] as const,
  migrationStatus: (id: string) => ['migrations', id, 'status'] as const,
};

/**
 * Fetch all platforms
 */
export function usePlatforms() {
  return useQuery({
    queryKey: queryKeys.platforms,
    queryFn: api.listPlatforms,
  });
}

/**
 * Add a new platform
 */
export function useAddPlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: PlatformConfig) => api.addPlatform(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
    },
  });
}

/**
 * Test platform connection
 */
export function useTestConnection() {
  return useMutation({
    mutationFn: (id: string) => api.testPlatformConnection(id),
  });
}

/**
 * Sync platform devices
 */
export function useSyncPlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.syncPlatformDevices(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
    },
  });
}

/**
 * Delete a platform
 */
export function useDeletePlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deletePlatform(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
    },
  });
}

/**
 * Fetch VMs for migration
 */
export function useVMs() {
  return useQuery({
    queryKey: queryKeys.vms,
    queryFn: api.listVMs,
  });
}

/**
 * Plan a migration
 */
export function usePlanMigration() {
  return useMutation({
    mutationFn: ({
      vmId,
      targetPlatformId,
    }: {
      vmId: string;
      targetPlatformId: string;
    }) => api.planMigration(vmId, targetPlatformId),
  });
}

/**
 * Execute a migration
 */
export function useExecuteMigration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (planId: string) => api.executeMigration(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.migrationHistory,
      });
    },
  });
}

/**
 * Get migration status (polled during execution)
 */
export function useMigrationStatus(id: string | null, enabled = false) {
  return useQuery({
    queryKey: queryKeys.migrationStatus(id ?? ''),
    queryFn: () => api.getMigrationStatus(id!),
    enabled: enabled && id !== null,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000; // Poll every 2 seconds while running
      }
      return false; // Stop polling when done
    },
  });
}

/**
 * Fetch migration history
 */
export function useMigrationHistory() {
  return useQuery({
    queryKey: queryKeys.migrationHistory,
    queryFn: api.getMigrationHistory,
  });
}

/**
 * Rollback a migration
 */
export function useRollbackMigration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.rollbackMigration(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.migrationHistory,
      });
    },
  });
}
