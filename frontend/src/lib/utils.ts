import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class names with Tailwind CSS conflict resolution
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration in seconds to human readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

/**
 * Format relative time from ISO string
 */
export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) return 'just now';
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
  return `${Math.floor(diffSeconds / 86400)} days ago`;
}

/**
 * Get platform type display info
 */
export function getPlatformTypeInfo(type: string): {
  label: string;
  icon: string;
  color: string;
} {
  switch (type) {
    case 'vsphere':
      return { label: 'VMware vSphere', icon: 'VM', color: 'text-blue-400' };
    case 'kvm':
      return { label: 'KVM/QEMU', icon: 'KV', color: 'text-orange-400' };
    case 'fusionsphere':
      return { label: 'Huawei FusionSphere', icon: 'FS', color: 'text-red-400' };
    default:
      return { label: type, icon: '??', color: 'text-gray-400' };
  }
}

/**
 * Get status color class
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'connected':
      return 'text-[var(--color-success)]';
    case 'disconnected':
      return 'text-[var(--color-text-secondary)]';
    case 'testing':
      return 'text-[var(--color-warning)]';
    case 'error':
      return 'text-[var(--color-danger)]';
    case 'completed':
      return 'text-[var(--color-success)]';
    case 'running':
      return 'text-[var(--color-accent)]';
    case 'failed':
      return 'text-[var(--color-danger)]';
    case 'pending':
      return 'text-[var(--color-warning)]';
    default:
      return 'text-[var(--color-text-secondary)]';
  }
}
