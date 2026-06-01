import React from 'react';
import { cn } from '@/lib/utils';
import { getPlatformTypeInfo, getStatusColor, formatRelativeTime } from '@/lib/utils';
import type { Platform } from '@/types/platform';

interface PlatformCardProps {
  platform: Platform;
  onTest: (id: string) => void;
  onEdit: (platform: Platform) => void;
  onSync: (id: string) => void;
  onDelete: (id: string) => void;
  isLoading?: boolean;
}

/**
 * Status indicator dot
 */
function StatusDot({ status }: { status: string }) {
  const colorClass = cn(
    'w-2.5 h-2.5 rounded-full',
    status === 'connected' && 'bg-[var(--color-success)]',
    status === 'disconnected' && 'bg-[var(--color-text-secondary)]',
    status === 'testing' && 'bg-[var(--color-warning)] animate-pulse',
    status === 'error' && 'bg-[var(--color-danger)]'
  );

  return <span className={colorClass} aria-label={`Status: ${status}`} />;
}

/**
 * Platform icon badge
 */
function PlatformIcon({ type }: { type: string }) {
  const info = getPlatformTypeInfo(type);

  return (
    <div
      className={cn(
        'w-10 h-10 rounded-lg flex items-center justify-center',
        'bg-[var(--color-bg-tertiary)] border border-[var(--color-border)]',
        'font-bold text-sm',
        info.color
      )}
      aria-label={info.label}
    >
      {info.icon}
    </div>
  );
}

/**
 * Device count display
 */
function DeviceCount({
  label,
  count,
}: {
  label: string;
  count: number;
}) {
  return (
    <div className="text-center">
      <div className="text-lg font-semibold text-[var(--color-text-primary)]">
        {count}
      </div>
      <div className="text-xs text-[var(--color-text-secondary)]">{label}</div>
    </div>
  );
}

/**
 * Action button for platform card
 */
function ActionButton({
  label,
  onClick,
  variant = 'default',
  disabled = false,
}: {
  label: string;
  onClick: () => void;
  variant?: 'default' | 'danger';
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={cn(
        'px-3 py-1.5 text-xs rounded-md transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]',
        variant === 'default' &&
          'bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] hover:bg-[var(--color-border)]',
        variant === 'danger' &&
          'bg-transparent text-[var(--color-danger)] hover:bg-red-900/20',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      {label}
    </button>
  );
}

/**
 * Platform card component displaying platform info and actions
 */
export function PlatformCard({
  platform,
  onTest,
  onEdit,
  onSync,
  onDelete,
  isLoading = false,
}: PlatformCardProps): React.JSX.Element {
  const platformInfo = getPlatformTypeInfo(platform.type);

  return (
    <article
      className={cn(
        'bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)]',
        'p-5 transition-all hover:border-[var(--color-accent)]/30',
        isLoading && 'opacity-60 pointer-events-none'
      )}
      aria-label={`${platformInfo.label} platform: ${platform.name}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <PlatformIcon type={platform.type} />
          <div>
            <h3 className="text-[var(--color-text-primary)] font-medium text-sm">
              {platform.name}
            </h3>
            <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">
              {platformInfo.label}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusDot status={platform.status} />
          <span
            className={cn('text-xs capitalize', getStatusColor(platform.status))}
          >
            {platform.status}
          </span>
        </div>
      </div>

      {/* Device counts */}
      <div className="flex justify-around py-3 border-y border-[var(--color-border)] mb-4">
        <DeviceCount label="VMs" count={platform.device_count.vms} />
        <DeviceCount label="Hosts" count={platform.device_count.hosts} />
        <DeviceCount label="Storage" count={platform.device_count.storage} />
      </div>

      {/* Connection info */}
      <div className="text-xs text-[var(--color-text-secondary)] mb-4 space-y-1">
        <div className="flex justify-between">
          <span>Host</span>
          <span className="text-[var(--color-text-primary)] font-mono">
            {platform.host}:{platform.port}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Last sync</span>
          <span className="text-[var(--color-text-primary)]">
            {formatRelativeTime(platform.last_sync)}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        <ActionButton
          label="Test"
          onClick={() => onTest(platform.id)}
          disabled={platform.status === 'testing'}
        />
        <ActionButton label="Edit" onClick={() => onEdit(platform)} />
        <ActionButton
          label="Sync"
          onClick={() => onSync(platform.id)}
          disabled={platform.status !== 'connected'}
        />
        <ActionButton
          label="Delete"
          onClick={() => onDelete(platform.id)}
          variant="danger"
        />
      </div>
    </article>
  );
}
