/**
 * Platform types for V3.2 SRE Platform
 */

export type PlatformType = 'vsphere' | 'kvm' | 'fusionsphere';
export type PlatformStatus = 'connected' | 'disconnected' | 'testing' | 'error';

export interface PlatformDeviceCount {
  vms: number;
  hosts: number;
  storage: number;
}

export interface Platform {
  id: string;
  name: string;
  type: PlatformType;
  host: string;
  port: number;
  status: PlatformStatus;
  device_count: PlatformDeviceCount;
  last_sync: string;
}

export interface PlatformConfig {
  name: string;
  type: PlatformType;
  host: string;
  port: number;
  username: string;
  password: string;
  verify_ssl: boolean;
}

export interface TestResult {
  success: boolean;
  latency_ms: number;
  version: string;
  details: Record<string, unknown>;
  error?: string;
}

export interface SyncResult {
  synced: number;
  created: number;
  updated: number;
  removed: number;
  duration_ms: number;
}

export interface MigrationStep {
  step: number;
  description: string;
  estimated_seconds: number;
}

export interface MigrationPlan {
  id: string;
  source_vm: {
    id: string;
    name: string;
    platform: string;
  };
  target_platform: string;
  tool: {
    name: string;
    description: string;
  };
  steps: MigrationStep[];
  risks: string[];
  estimated_time_seconds: number;
}

export type MigrationStatus = 'pending' | 'running' | 'completed' | 'failed' | 'rolled_back';

export interface MigrationExecution {
  id: string;
  plan: MigrationPlan;
  status: MigrationStatus;
  current_step: number;
  started_at: string;
  completed_at?: string;
  error?: string;
  log: Array<{
    timestamp: string;
    message: string;
    level: 'info' | 'warn' | 'error';
  }>;
}

export interface MigrationHistoryItem {
  id: string;
  source_vm: { id: string; name: string };
  source_platform: string;
  target_platform: string;
  status: MigrationStatus;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  tool: string;
}

export interface Device {
  id: string;
  name: string;
  type: 'vm' | 'host' | 'storage';
  platform_id: string;
  status: string;
  properties: Record<string, unknown>;
}

export interface CSVImportMapping {
  source_column: string;
  target_field: string;
  transform?: string;
}

export interface PlatformStore {
  platforms: Platform[];
  selectedPlatform: Platform | null;
  wizardOpen: boolean;
  importDialogOpen: boolean;
  setPlatforms: (platforms: Platform[]) => void;
  setSelectedPlatform: (platform: Platform | null) => void;
  setWizardOpen: (open: boolean) => void;
  setImportDialogOpen: (open: boolean) => void;
}

export interface MigrationStore {
  selectedVM: Device | null;
  targetPlatform: Platform | null;
  currentPlan: MigrationPlan | null;
  execution: MigrationExecution | null;
  setSelectedVM: (vm: Device | null) => void;
  setTargetPlatform: (platform: Platform | null) => void;
  setCurrentPlan: (plan: MigrationPlan | null) => void;
  setExecution: (execution: MigrationExecution | null) => void;
  reset: () => void;
}
