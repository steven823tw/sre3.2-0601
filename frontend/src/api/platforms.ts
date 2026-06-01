import { httpClient } from './client';
import type {
  Platform,
  PlatformConfig,
  TestResult,
  SyncResult,
  MigrationPlan,
  MigrationExecution,
  MigrationHistoryItem,
  Device,
} from '@/types/platform';

export async function listPlatforms(): Promise<Platform[]> {
  return httpClient.get<Platform[]>('/platforms/');
}

export async function getPlatform(id: string): Promise<Platform> {
  return httpClient.get<Platform>(`/platforms/${id}`);
}

export async function addPlatform(config: PlatformConfig): Promise<Platform> {
  return httpClient.post<Platform>('/platforms/', config);
}

export async function updatePlatform(id: string, config: Partial<PlatformConfig>): Promise<Platform> {
  return httpClient.put<Platform>(`/platforms/${id}`, config);
}

export async function testPlatformConnection(id: string): Promise<TestResult> {
  return httpClient.post<TestResult>(`/platforms/${id}/test`);
}

export async function syncPlatformDevices(id: string): Promise<SyncResult> {
  return httpClient.post<SyncResult>(`/platforms/${id}/sync`);
}

export async function deletePlatform(id: string): Promise<void> {
  return httpClient.delete<void>(`/platforms/${id}`);
}

export async function listDevices(platformId?: string, deviceType?: string): Promise<Device[]> {
  const params: Record<string, string> = {};
  if (platformId) params.platform_id = platformId;
  if (deviceType) params.type = deviceType;
  return httpClient.get<Device[]>('/devices/', params);
}

export async function listVMs(): Promise<Device[]> {
  return listDevices(undefined, 'vm');
}

export async function planMigration(vmId: string, targetPlatformId: string): Promise<MigrationPlan> {
  return httpClient.post<MigrationPlan>('/migration/plan', {
    source_vm_id: vmId,
    target_platform_id: targetPlatformId,
  });
}

export async function executeMigration(planId: string): Promise<MigrationExecution> {
  return httpClient.post<MigrationExecution>(`/migration/execute?plan_id=${planId}`);
}

export async function getMigrationStatus(id: string): Promise<MigrationExecution> {
  return httpClient.get<MigrationExecution>(`/migration/${id}`);
}

export async function getMigrationHistory(): Promise<MigrationHistoryItem[]> {
  return httpClient.get<MigrationHistoryItem[]>('/migration/history');
}

export async function rollbackMigration(id: string): Promise<void> {
  return httpClient.post<void>(`/migration/${id}/rollback`);
}

/**
 * Import devices via CSV file upload.
 *
 * Uses raw fetch() instead of httpClient because FormData requires the browser
 * to set the Content-Type header (with multipart boundary) automatically.
 * httpClient always sets Content-Type: application/json, which would break
 * multipart/form-data uploads. The auth token is read from the same
 * localStorage key ("auth_token") that httpClient uses, keeping auth consistent.
 */
export async function importDevicesCSV(
  platformId: string,
  file: File,
  mappings: Record<string, string>
): Promise<{ imported: number; errors: string[] }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mappings', JSON.stringify(mappings));
  const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';
  const token = localStorage.getItem('auth_token');
  const response = await fetch(`${BASE_URL}/platforms/${platformId}/import/csv`, {
    method: 'POST',
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Import failed: ${errorBody}`);
  }
  return response.json();
}
