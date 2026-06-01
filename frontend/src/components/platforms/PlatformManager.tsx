import React, { useState, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { usePlatforms, useTestConnection, useSyncPlatform, useDeletePlatform } from '../../lib/queries';
import { usePlatformStore } from '../../lib/stores';
import PlatformCard from './PlatformCard';
import PlatformWizard from './PlatformWizard';
import DeviceImport from './DeviceImport';
import type { Platform } from '../../types/platform';

export default function PlatformManager(): React.JSX.Element {
  const { data: platforms, isLoading, error } = usePlatforms();
  const { wizardOpen, setWizardOpen, importDialogOpen, setImportDialogOpen, selectedPlatform, setSelectedPlatform } = usePlatformStore();
  const testMutation = useTestConnection();
  const syncMutation = useSyncPlatform();
  const deleteMutation = useDeletePlatform();
  const [testResults, setTestResults] = useState<Record<string, string>>({});

  const handleTest = useCallback((id: string) => {
    setTestResults((prev) => ({ ...prev, [id]: 'testing' }));
    testMutation.mutate(id, {
      onSuccess: (result) => {
        setTestResults((prev) => ({ ...prev, [id]: result.success ? 'success' : 'failed' }));
        setTimeout(() => setTestResults((prev) => { const next = { ...prev }; delete next[id]; return next; }), 3000);
      },
      onError: () => {
        setTestResults((prev) => ({ ...prev, [id]: 'failed' }));
        setTimeout(() => setTestResults((prev) => { const next = { ...prev }; delete next[id]; return next; }), 3000);
      },
    });
  }, [testMutation]);

  const handleEdit = useCallback((platform: Platform) => {
    setSelectedPlatform(platform);
    setWizardOpen(true);
  }, [setSelectedPlatform, setWizardOpen]);

  const handleSync = useCallback((id: string) => {
    syncMutation.mutate(id);
  }, [syncMutation]);

  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Are you sure you want to delete this platform? This action cannot be undone.')) {
      deleteMutation.mutate(id);
    }
  }, [deleteMutation]);

  const handleImport = useCallback((platform: Platform) => {
    setSelectedPlatform(platform);
    setImportDialogOpen(true);
  }, [setSelectedPlatform, setImportDialogOpen]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[var(--color-text-secondary)]">Loading platforms...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center p-6 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)]">
          <svg className="w-12 h-12 text-[var(--color-danger)] mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Failed to load platforms</h3>
          <p className="text-sm text-[var(--color-text-secondary)]">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Platform Manager</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">Manage virtualization platforms and devices</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setImportDialogOpen(true)} className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] hover:bg-[var(--color-border)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Import devices">
            Import Devices
          </button>
          <button onClick={() => setWizardOpen(true)} className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Add platform">
            Add Platform
          </button>
        </div>
      </div>

      {!platforms || platforms.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)]">
          <svg className="w-16 h-16 text-[var(--color-text-secondary)] mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">No platforms configured</h3>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">Add your first virtualization platform to get started</p>
          <button onClick={() => setWizardOpen(true)} className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Add first platform">
            Add Platform
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {platforms.map((platform) => (
            <div key={platform.id} className="relative">
              <PlatformCard
                platform={platform}
                onTest={handleTest}
                onEdit={handleEdit}
                onSync={handleSync}
                onDelete={handleDelete}
                isLoading={testResults[platform.id] === 'testing'}
              />
              {testResults[platform.id] && testResults[platform.id] !== 'testing' && (
                <div className={cn(
                  'absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium',
                  testResults[platform.id] === 'success' ? 'bg-green-900/50 text-[var(--color-success)]' : 'bg-red-900/50 text-[var(--color-danger)]'
                )}>
                  {testResults[platform.id] === 'success' ? 'Connected' : 'Failed'}
                </div>
              )}
              <button onClick={() => handleImport(platform)} className="absolute bottom-16 right-4 px-2 py-1 rounded text-xs bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)] transition-colors" aria-label={'Import devices from ' + platform.name}>
                Import
              </button>
            </div>
          ))}
        </div>
      )}

      <PlatformWizard isOpen={wizardOpen} onClose={() => setWizardOpen(false)} onComplete={() => setWizardOpen(false)} />
      <DeviceImport isOpen={importDialogOpen} platform={selectedPlatform} onClose={() => { setImportDialogOpen(false); setSelectedPlatform(null); }} onComplete={() => { setImportDialogOpen(false); setSelectedPlatform(null); }} />
    </div>
  );
}
