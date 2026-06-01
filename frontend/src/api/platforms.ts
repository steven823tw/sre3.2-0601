import type {
  Platform,
  PlatformConfig,
  TestResult,
  SyncResult,
  MigrationPlan,
  MigrationExecution,
  MigrationHistoryItem,
  Device,
} from '../types/platform';

const API_BASE = '/api/v1';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    let message = `API error: ${response.status}`;
    try {
      const parsed = JSON.parse(errorBody);
      message = parsed.detail || parsed.message || message;
    } catch {
      // Use default message if response body is not JSON
    }
    throw new Error(message);
  }

  return response.json();
}

/**
 * List all configured platforms
 */
export async function listPlatforms(): Promise<Platform[]> {
  return fetchJSON<Platform[]>(`${API_BASE}/platforms/`);
}

/**
 * Get a single platform by ID
 */
export async function getPlatform(id: string): Promise<Platform> {
  return fetchJSON<Platform>(`${API_BASE}/platforms/${id}`);
}

/**
 * Add a new platform configuration
 */
export async function addPlatform(config: PlatformConfig): Promise<Platform> {
  return fetchJSON<Platform>(`${API_BASE}/platforms/`, {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

/**
 * Update an existing platform configuration
 */
export async function updatePlatform(
  id: string,
  config: Partial<PlatformConfig>
): Promise<Platform> {
  return fetchJSON<Platform>(`${API_BASE}/platforms/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(config),
  });
}

/**
 * Test connection to a platform
 */
export async function testPlatformConnection(id: string): Promise<TestResult> {
  return fetchJSON<TestResult>(`${API_BASE}/platforms/${id}/test`, {
    method: 'POST',
  });
}

/**
 * Sync devices from a platform
 */
export async function syncPlatformDevices(id: string): Promise<SyncResult> {
  return fetchJSON<SyncResult>(`${API_BASE}/platforms/${id}/sync`, {
    method: 'POST',
  });
}

/**
 * Delete a platform
 */
export async function deletePlatform(id: string): Promise<void> {
  await fetchJSON<void>(`${API_BASE}/platforms/${id}`, {
    method: 'DELETE',
  });
}

/**
 * List devices from a platform
 */
export async function listDevices(
  platformId?: string,
  deviceType?: string
): Promise<Device[]> {
  const params = new URLSearchParams();
  if (platformId) params.set('platform_id', platformId);
  if (deviceType) params.set('type', deviceType);
  const query = params.toString();
  return fetchJSON<Device[]>(`${API_BASE}/devices/${query ? `?${query}` : ''}`);
}

/**
 * Get VMs for migration selection
 */
export async function listVMs(): Promise<Device[]> {
  return listDevices(undefined, 'vm');
}

/**
 * Plan a migration
 */
export async function planMigration(
  vmId: string,
  targetPlatformId: string
): Promise<MigrationPlan> {
  return fetchJSON<MigrationPlan>(`${API_BASE}/migrations/plan`, {
    method: 'POST',
    body: JSON.stringify({
      source_vm_id: vmId,
      target_platform_id: targetPlatformId,
    }),
  });
}

/**
 * Execute a migration plan
 */
export async function executeMigration(planId: string): Promise<MigrationExecution> {
  return fetchJSON<MigrationExecution>(`${API_BASE}/migrations/execute`, {
    method: 'POST',
    body: JSON.stringify({ plan_id: planId }),
  });
}

/**
 * Get migration execution status
 */
export async function getMigrationStatus(id: string): Promise<MigrationExecution> {
  return fetchJSON<MigrationExecution>(`${API_BASE}/migrations/${id}/status`);
}

/**
 * Get migration history
 */
export async function getMigrationHistory(): Promise<MigrationHistoryItem[]> {
  return fetchJSON<MigrationHistoryItem[]>(`${API_BASE}/migrations/history`);
}

/**
 * Rollback a migration
 */
export async function rollbackMigration(id: string): Promise<void> {
  await fetchJSON<void>(`${API_BASE}/migrations/${id}/rollback`, {
    method: 'POST',
  });
}

/**
 * Import devices from CSV
 */
export async function importDevicesCSV(
  platformId: string,
  file: File,
  mappings: Record<string, string>
): Promise<{ imported: number; errors: string[] }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mappings', JSON.stringify(mappings));

  const response = await fetch(`${API_BASE}/platforms/${platformId}/import/csv`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Import failed: ${errorBody}`);
  }

  return response.json();
}
