import React, { useState, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { formatDuration, formatRelativeTime, getStatusColor } from '../../lib/utils';
import { useMigrationHistory, useRollbackMigration } from '../../lib/queries';
import type { MigrationHistoryItem, MigrationStatus } from '../../types/platform';

interface MigrationHistoryProps {
  onViewDetails?: (id: string) => void;
}

function StatusBadge({ status }: { status: MigrationStatus }): React.JSX.Element {
  const config: Record<MigrationStatus, { label: string; className: string }> = {
    pending: { label: 'Pending', className: 'bg-yellow-900/30 text-[var(--color-warning)]' },
    running: { label: 'Running', className: 'bg-blue-900/30 text-[var(--color-accent)]' },
    completed: { label: 'Completed', className: 'bg-green-900/30 text-[var(--color-success)]' },
    failed: { label: 'Failed', className: 'bg-red-900/30 text-[var(--color-danger)]' },
    rolled_back: { label: 'Rolled Back', className: 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]' },
  };
  const { label, className } = config[status];
  return <span className={cn('px-2 py-0.5 rounded text-xs font-medium', className)}>{label}</span>;
}

function EmptyState(): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-16 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)]">
      <svg className="w-16 h-16 text-[var(--color-text-secondary)] mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">No migration history</h3>
      <p className="text-sm text-[var(--color-text-secondary)]">Completed migrations will appear here</p>
    </div>
  );
}

export default function MigrationHistory({ onViewDetails }: MigrationHistoryProps): React.JSX.Element {
  const { data: history, isLoading, error } = useMigrationHistory();
  const rollbackMutation = useRollbackMigration();
  const [rollingBackId, setRollingBackId] = useState<string | null>(null);

  const handleRollback = useCallback((id: string) => {
    if (!window.confirm('Are you sure you want to rollback this migration? This may cause service disruption.')) return;
    setRollingBackId(id);
    rollbackMutation.mutate(id, {
      onSettled: () => setRollingBackId(null),
    });
  }, [rollbackMutation]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[var(--color-text-secondary)]">Loading migration history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-center p-6 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)]">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Failed to load history</h3>
          <p className="text-sm text-[var(--color-text-secondary)]">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!history || history.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Migration History</h2>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1">View and manage past migrations</p>
      </div>
      <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)] overflow-hidden">
        <table className="w-full" role="table" aria-label="Migration history">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">VM</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Migration</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Duration</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">When</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">

            {history.map((item) => (
              <tr key={item.id} className="hover:bg-[var(--color-bg-tertiary)]/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="text-sm font-medium text-[var(--color-text-primary)]">{item.source_vm.name}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-[var(--color-text-primary)]">{item.source_platform}</span>
                    <svg className="w-4 h-4 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                    <span className="text-[var(--color-text-primary)]">{item.target_platform}</span>
                  </div>
                  <div className="text-xs text-[var(--color-text-secondary)] mt-0.5">{item.tool}</div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={item.status} />
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-[var(--color-text-primary)]">
                    {item.duration_seconds ? formatDuration(item.duration_seconds) : '-'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-[var(--color-text-secondary)]">{formatRelativeTime(item.started_at)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {onViewDetails && (
                      <button onClick={() => onViewDetails(item.id)} className="px-2 py-1 rounded text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label={'View details for ' + item.source_vm.name}>
                        View
                      </button>
                    )}
                    {(item.status === 'completed' || item.status === 'failed') && (
                      <button onClick={() => handleRollback(item.id)} disabled={rollingBackId === item.id} className={cn('px-2 py-1 rounded text-xs transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', rollingBackId === item.id ? 'text-[var(--color-text-secondary)] cursor-not-allowed' : 'text-[var(--color-danger)] hover:bg-red-900/20')} aria-label={'Rollback ' + item.source_vm.name}>
                        {rollingBackId === item.id ? 'Rolling back...' : 'Rollback'}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
