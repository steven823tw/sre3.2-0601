import React, { useState, useCallback, useRef } from 'react';
import { cn } from '../../lib/utils';
import { useSyncPlatform } from '../../lib/queries';
import { importDevicesCSV } from '../../api/platforms';
import type { Platform, CSVImportMapping } from '../../types/platform';

interface DeviceImportProps {
  isOpen: boolean;
  platform: Platform | null;
  onClose: () => void;
  onComplete: () => void;
}

type ImportTab = 'sync' | 'csv' | 'manual';

const DEVICE_FIELDS = ['name', 'type', 'ip_address', 'os', 'cpu', 'memory', 'disk'];

function TabButton({ label, isActive, onClick }: { label: string; isActive: boolean; onClick: () => void }): React.JSX.Element {
  return (
    <button
      onClick={onClick}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]',
        isActive
          ? 'text-[var(--color-accent)] border-b-2 border-[var(--color-accent)]'
          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
      )}
      aria-label={label}
      aria-selected={isActive}
      role="tab"
    >
      {label}
    </button>
  );
}

function SyncTab({ platform, onComplete }: { platform: Platform; onComplete: () => void }): React.JSX.Element {
  const syncMutation = useSyncPlatform();
  const handleSync = useCallback(() => {
    syncMutation.mutate(platform.id, { onSuccess: () => onComplete() });
  }, [syncMutation, platform.id, onComplete]);

  return (
    <div className="space-y-4">
      <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4">
        <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Auto-discover devices</h4>
        <p className="text-xs text-[var(--color-text-secondary)] mb-4">
          Automatically discover and import all VMs, hosts, and storage from {platform.name}.
          This will sync the latest device inventory from the platform.
        </p>
        <div className="flex items-center gap-3 text-xs text-[var(--color-text-secondary)]">
          <span>Current devices: {platform.device_count.vms} VMs, {platform.device_count.hosts} hosts, {platform.device_count.storage} storage</span>
        </div>
      </div>
      <button
        onClick={handleSync}
        disabled={syncMutation.isPending || platform.status !== 'connected'}
        className={cn(
          'w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]',
          syncMutation.isPending || platform.status !== 'connected'
            ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed'
            : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90'
        )}
        aria-label="Start device sync"
      >
        {syncMutation.isPending ? 'Syncing...' : 'Sync Now'}
      </button>
      {syncMutation.error && (
        <p className="text-sm text-[var(--color-danger)]">{syncMutation.error.message}</p>
      )}
    </div>
  );
}

function CSVTab({ platform, onComplete }: { platform: Platform; onComplete: () => void }): React.JSX.Element {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<string[][]>([]);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setError(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const lines = text.split('
').filter((l) => l.trim());
      if (lines.length > 0) {
        const hdrs = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));
        setHeaders(hdrs);
        setPreview(lines.slice(1, 6).map((l) => l.split(',').map((c) => c.trim().replace(/"/g, ''))));
        const initialMappings: Record<string, string> = {};
        hdrs.forEach((h) => {
          const match = DEVICE_FIELDS.find((f) => f.toLowerCase() === h.toLowerCase());
          if (match) initialMappings[h] = match;
        });
        setMappings(initialMappings);
      }
    };
    reader.readAsText(selectedFile);
  }, []);

  const handleImport = useCallback(async () => {
    if (!file) return;
    setImporting(true);
    setError(null);
    try {
      await importDevicesCSV(platform.id, file, mappings);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  }, [file, platform.id, mappings, onComplete]);

  return (
    <div className="space-y-4">
      <div>
        <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileChange} className="hidden" aria-label="Upload CSV file" />
        <button onClick={() => fileInputRef.current?.click()} className={cn('w-full py-8 border-2 border-dashed border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-secondary)] hover:border-[var(--color-accent)]/50 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]')} aria-label="Select CSV file">
          {file ? file.name : 'Click to upload CSV file'}
        </button>
      </div>
      {headers.length > 0 && (
        <>
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Field Mapping</h4>
            <div className="space-y-2">
              {headers.map((header) => (
                <div key={header} className="flex items-center gap-3">
                  <span className="text-xs text-[var(--color-text-secondary)] w-1/3 truncate">{header}</span>
                  <select value={mappings[header] || ''} onChange={(e) => setMappings((prev) => ({ ...prev, [header]: e.target.value }))} className="flex-1 px-2 py-1 rounded text-xs bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label={'Map ' + header}>
                    <option value="">-- Skip --</option>
                    {DEVICE_FIELDS.map((f) => (<option key={f} value={f}>{f}</option>))}
                  </select>
                </div>
              ))}
            </div>
          </div>
          {preview.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Preview</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      {headers.map((h) => (<th key={h} className="px-2 py-1 text-left text-[var(--color-text-secondary)]">{h}</th>))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, i) => (
                      <tr key={i} className="border-b border-[var(--color-border)]">
                        {row.map((cell, j) => (<td key={j} className="px-2 py-1 text-[var(--color-text-primary)]">{cell}</td>))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          <button onClick={handleImport} disabled={importing} className={cn('w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', importing ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Import devices from CSV">
            {importing ? 'Importing...' : 'Import'}
          </button>
        </>
      )}
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
    </div>
  );
}

function ManualTab({ platform, onComplete }: { platform: Platform; onComplete: () => void }): React.JSX.Element {
  const [formData, setFormData] = useState({ name: '', type: 'vm', ip_address: '', os: '', cpu: '', memory: '', disk: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/devices/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, platform_id: platform.id }),
      });
      if (!response.ok) throw new Error('Failed to add device');
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add device');
    } finally {
      setSaving(false);
    }
  }, [formData, platform.id, onComplete]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="device-name" className="block text-sm text-[var(--color-text-secondary)] mb-1">Device Name</label>
        <input id="device-name" type="text" value={formData.name} onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))} placeholder="web-server-01" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Device name" required />
      </div>
      <div>
        <label htmlFor="device-type" className="block text-sm text-[var(--color-text-secondary)] mb-1">Type</label>
        <select id="device-type" value={formData.type} onChange={(e) => setFormData((p) => ({ ...p, type: e.target.value }))} className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Device type">
          <option value="vm">Virtual Machine</option>
          <option value="host">Host</option>
          <option value="storage">Storage</option>
        </select>
      </div>
      <div>
        <label htmlFor="device-ip" className="block text-sm text-[var(--color-text-secondary)] mb-1">IP Address</label>
        <input id="device-ip" type="text" value={formData.ip_address} onChange={(e) => setFormData((p) => ({ ...p, ip_address: e.target.value }))} placeholder="192.168.1.100" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="IP address" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label htmlFor="device-cpu" className="block text-sm text-[var(--color-text-secondary)] mb-1">CPU</label>
          <input id="device-cpu" type="text" value={formData.cpu} onChange={(e) => setFormData((p) => ({ ...p, cpu: e.target.value }))} placeholder="4 vCPU" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="CPU" />
        </div>
        <div>
          <label htmlFor="device-mem" className="block text-sm text-[var(--color-text-secondary)] mb-1">Memory</label>
          <input id="device-mem" type="text" value={formData.memory} onChange={(e) => setFormData((p) => ({ ...p, memory: e.target.value }))} placeholder="8 GB" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Memory" />
        </div>
        <div>
          <label htmlFor="device-disk" className="block text-sm text-[var(--color-text-secondary)] mb-1">Disk</label>
          <input id="device-disk" type="text" value={formData.disk} onChange={(e) => setFormData((p) => ({ ...p, disk: e.target.value }))} placeholder="100 GB" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Disk" />
        </div>
      </div>
      <button type="submit" disabled={saving || !formData.name} className={cn('w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', saving || !formData.name ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Add device">
        {saving ? 'Adding...' : 'Add Device'}
      </button>
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
    </form>
  );
}

export default function DeviceImport({ isOpen, platform, onClose, onComplete }: DeviceImportProps): React.JSX.Element | null {
  const [activeTab, setActiveTab] = useState<ImportTab>('sync');

  if (!isOpen || !platform) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Import devices">
      <div className="w-full max-w-lg mx-4 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)] shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Import Devices</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-[var(--color-bg-tertiary)] transition-colors" aria-label="Close dialog">
            <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="flex border-b border-[var(--color-border)]">
          <TabButton label="Sync" isActive={activeTab === 'sync'} onClick={() => setActiveTab('sync')} />
          <TabButton label="CSV Import" isActive={activeTab === 'csv'} onClick={() => setActiveTab('csv')} />
          <TabButton label="Manual" isActive={activeTab === 'manual'} onClick={() => setActiveTab('manual')} />
        </div>
        <div className="p-4">
          {activeTab === 'sync' && <SyncTab platform={platform} onComplete={onComplete} />}
          {activeTab === 'csv' && <CSVTab platform={platform} onComplete={onComplete} />}
          {activeTab === 'manual' && <ManualTab platform={platform} onComplete={onComplete} />}
        </div>
      </div>
    </div>
  );
}
