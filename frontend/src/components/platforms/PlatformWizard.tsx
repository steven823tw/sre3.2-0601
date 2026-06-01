import React, { useState, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { getPlatformTypeInfo } from '../../lib/utils';
import { useAddPlatform, useTestConnection } from '../../lib/queries';
import TestConnection from './TestConnection';
import type { PlatformType, PlatformConfig, TestResult } from '../../types/platform';

interface PlatformWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const PLATFORM_OPTIONS: Array<{ type: PlatformType; description: string }> = [
  { type: 'vsphere', description: 'VMware vSphere virtualization platform with ESXi hosts and vCenter management' },
  { type: 'kvm', description: 'KVM/QEMU open-source virtualization for Linux-based infrastructure' },
  { type: 'fusionsphere', description: 'Huawei FusionSphere enterprise cloud platform for hybrid cloud deployments' },
];

const SYNC_INTERVALS = [
  { value: '5', label: 'Every 5 minutes' },
  { value: '15', label: 'Every 15 minutes' },
  { value: '30', label: 'Every 30 minutes' },
  { value: '60', label: 'Every hour' },
  { value: '360', label: 'Every 6 hours' },
  { value: '1440', label: 'Every 24 hours' },
];

const SYNC_SCOPES = [
  { value: 'all', label: 'All resources' },
  { value: 'clusters', label: 'Clusters only' },
  { value: 'resource_pools', label: 'Resource pools only' },
];


function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }): React.JSX.Element {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: totalSteps }, (_, i) => (
        <React.Fragment key={i}>
          <div
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
              i < currentStep && 'bg-[var(--color-accent)] text-[var(--color-bg-primary)]',
              i === currentStep && 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border-2 border-[var(--color-accent)]',
              i > currentStep && 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]'
            )}
            aria-label={'Step ' + (i + 1) + (i === currentStep ? ' (current)' : '')}
          >
            {i < currentStep ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              i + 1
            )}
          </div>
          {i < totalSteps - 1 && (
            <div className={cn('w-12 h-0.5', i < currentStep ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border)]')} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function StepNavigation({
  onBack, onNext, isFirst, isLast, nextDisabled = false, nextLabel,
}: {
  onBack: () => void; onNext: () => void; isFirst: boolean; isLast: boolean;
  nextDisabled?: boolean; nextLabel?: string;
}): React.JSX.Element {
  return (
    <div className="flex justify-between mt-6 pt-4 border-t border-[var(--color-border)]">
      <button onClick={onBack} disabled={isFirst} className={cn('px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', isFirst ? 'text-[var(--color-text-secondary)] cursor-not-allowed' : 'text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]')} aria-label="Go back">
        Back
      </button>
      <button onClick={onNext} disabled={nextDisabled} className={cn('px-6 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', nextDisabled ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label={isLast ? 'Save platform' : 'Continue to next step'}>
        {nextLabel || (isLast ? 'Save' : 'Next')}
      </button>
    </div>
  );
}

function StepSelectType({ selected, onSelect, onNext, onBack, isFirst, isLast }: {
  selected: PlatformType | null; onSelect: (type: PlatformType) => void;
  onNext: () => void; onBack: () => void; isFirst: boolean; isLast: boolean;
}): React.JSX.Element {
  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Select Platform Type</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Choose the virtualization platform you want to add</p>
      <div className="space-y-3">
        {PLATFORM_OPTIONS.map((option) => {
          const info = getPlatformTypeInfo(option.type);
          return (
            <button key={option.type} onClick={() => onSelect(option.type)} className={cn('w-full p-4 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', selected === option.type ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10' : 'border-[var(--color-border)] bg-[var(--color-bg-tertiary)] hover:border-[var(--color-accent)]/50')} aria-label={'Select ' + info.label} aria-pressed={selected === option.type}>
              <div className="flex items-center gap-3">
                <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center bg-[var(--color-bg-primary)] font-bold text-sm', info.color)}>{info.icon}</div>
                <div>
                  <div className="text-sm font-medium text-[var(--color-text-primary)]">{info.label}</div>
                  <div className="text-xs text-[var(--color-text-secondary)] mt-1">{option.description}</div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      <StepNavigation onBack={onBack} onNext={onNext} isFirst={isFirst} isLast={isLast} nextDisabled={!selected} />
    </div>
  );
}

function StepConnectionConfig({ config, onChange, onNext, onBack, isFirst, isLast }: {
  config: Partial<PlatformConfig>; onChange: (updates: Partial<PlatformConfig>) => void;
  onNext: () => void; onBack: () => void; isFirst: boolean; isLast: boolean;
}): React.JSX.Element {
  const testMutation = useTestConnection();
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const handleTest = useCallback(() => { testMutation.mutate('test', { onSuccess: (result) => setTestResult(result) }); }, [testMutation]);
  const isValid = config.host && config.port && config.username && config.password && config.name;
  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Connection Configuration</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Enter the connection details for your platform</p>
      <div className="space-y-4">
        <div>
          <label htmlFor="platform-name" className="block text-sm text-[var(--color-text-secondary)] mb-1">Platform Name</label>
          <input id="platform-name" type="text" value={config.name || ''} onChange={(e) => onChange({ name: e.target.value })} placeholder="Production vCenter" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Platform name" required />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label htmlFor="platform-host" className="block text-sm text-[var(--color-text-secondary)] mb-1">Host</label>
            <input id="platform-host" type="text" value={config.host || ''} onChange={(e) => onChange({ host: e.target.value })} placeholder="vcenter.example.com" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Platform host address" required />
          </div>
          <div>
            <label htmlFor="platform-port" className="block text-sm text-[var(--color-text-secondary)] mb-1">Port</label>
            <input id="platform-port" type="number" value={config.port || ''} onChange={(e) => onChange({ port: parseInt(e.target.value, 10) })} placeholder="443" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Platform port number" required />
          </div>
        </div>
        <div>
          <label htmlFor="platform-username" className="block text-sm text-[var(--color-text-secondary)] mb-1">Username</label>
          <input id="platform-username" type="text" value={config.username || ''} onChange={(e) => onChange({ username: e.target.value })} placeholder="administrator@vsphere.local" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Username" autoComplete="username" required />
        </div>
        <div>
          <label htmlFor="platform-password" className="block text-sm text-[var(--color-text-secondary)] mb-1">Password</label>
          <input id="platform-password" type="password" value={config.password || ''} onChange={(e) => onChange({ password: e.target.value })} placeholder="Enter password" className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Password" autoComplete="current-password" required />
        </div>
        <div className="flex items-center gap-3">
          <button type="button" role="switch" aria-checked={config.verify_ssl ?? true} aria-label="Verify SSL certificate" onClick={() => onChange({ verify_ssl: !(config.verify_ssl ?? true) })} className={cn('relative w-11 h-6 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', config.verify_ssl ?? true ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-bg-tertiary)]')}>
            <span className={cn('absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform', (config.verify_ssl ?? true) && 'translate-x-5')} />
          </button>
          <span className="text-sm text-[var(--color-text-primary)]">Verify SSL certificate</span>
        </div>
        <div className="pt-2">
          <button onClick={handleTest} disabled={!isValid || testMutation.isPending} className={cn('px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', !isValid || testMutation.isPending ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] hover:bg-[var(--color-border)]')} aria-label="Test connection">
            {testMutation.isPending ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
        <TestConnection isLoading={testMutation.isPending} result={testResult} error={testMutation.error?.message || null} onRetry={handleTest} />
      </div>
      <StepNavigation onBack={onBack} onNext={onNext} isFirst={isFirst} isLast={isLast} nextDisabled={!isValid} />
    </div>
  );
}

function StepSyncOptions({ syncInterval, syncScope, onIntervalChange, onScopeChange, onNext, onBack, isFirst, isLast }: {
  syncInterval: string; syncScope: string; onIntervalChange: (v: string) => void; onScopeChange: (v: string) => void;
  onNext: () => void; onBack: () => void; isFirst: boolean; isLast: boolean;
}): React.JSX.Element {
  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Sync Options</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Configure how often devices are synchronized</p>
      <div className="space-y-4">
        <div>
          <label htmlFor="sync-interval" className="block text-sm text-[var(--color-text-secondary)] mb-1">Auto-sync Interval</label>
          <select id="sync-interval" value={syncInterval} onChange={(e) => onIntervalChange(e.target.value)} className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Auto-sync interval">
            {SYNC_INTERVALS.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-[var(--color-text-secondary)] mb-2">Sync Scope</label>
          <div className="space-y-2">
            {SYNC_SCOPES.map((opt) => (
              <label key={opt.value} className={cn('flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-colors', syncScope === opt.value ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10' : 'border-[var(--color-border)] bg-[var(--color-bg-tertiary)] hover:border-[var(--color-accent)]/50')}>
                <input type="radio" name="sync-scope" value={opt.value} checked={syncScope === opt.value} onChange={(e) => onScopeChange(e.target.value)} className="w-4 h-4 text-[var(--color-accent)]" aria-label={opt.label} />
                <span className="text-sm text-[var(--color-text-primary)]">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
      <StepNavigation onBack={onBack} onNext={onNext} isFirst={isFirst} isLast={isLast} />
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }): React.JSX.Element {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[var(--color-text-secondary)]">{label}</span>
      <span className="text-[var(--color-text-primary)] font-medium">{value}</span>
    </div>
  );
}

function StepConfirm({ config, syncInterval, syncScope, onSave, onBack, isFirst, isLast, isSaving }: {
  config: Partial<PlatformConfig>; syncInterval: string; syncScope: string;
  onSave: () => void; onBack: () => void; isFirst: boolean; isLast: boolean; isSaving: boolean;
}): React.JSX.Element {
  const platformInfo = config.type ? getPlatformTypeInfo(config.type) : null;
  const intervalLabel = SYNC_INTERVALS.find((i) => i.value === syncInterval)?.label || syncInterval;
  const scopeLabel = SYNC_SCOPES.find((s) => s.value === syncScope)?.label || syncScope;
  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Confirm &amp; Save</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Review your configuration before saving</p>
      <div className="space-y-3 bg-[var(--color-bg-tertiary)] rounded-lg p-4">
        <SummaryRow label="Platform" value={platformInfo?.label || ''} />
        <SummaryRow label="Name" value={config.name || ''} />
        <SummaryRow label="Host" value={(config.host || '') + ':' + String(config.port || '')} />
        <SummaryRow label="Username" value={config.username || ''} />
        <SummaryRow label="SSL Verify" value={config.verify_ssl ? 'Enabled' : 'Disabled'} />
        <SummaryRow label="Sync Interval" value={intervalLabel} />
        <SummaryRow label="Sync Scope" value={scopeLabel} />
      </div>
      <StepNavigation onBack={onBack} onNext={onSave} isFirst={isFirst} isLast={isLast} nextLabel={isSaving ? 'Saving...' : 'Save Platform'} nextDisabled={isSaving} />
    </div>
  );
}

export default function PlatformWizard({ isOpen, onClose, onComplete }: PlatformWizardProps): React.JSX.Element | null {
  const [currentStep, setCurrentStep] = useState(0);
  const [platformType, setPlatformType] = useState<PlatformType | null>(null);
  const [config, setConfig] = useState<Partial<PlatformConfig>>({ verify_ssl: true });
  const [syncInterval, setSyncInterval] = useState('60');
  const [syncScope, setSyncScope] = useState('all');
  const addPlatformMutation = useAddPlatform();

  const handleConfigChange = useCallback((updates: Partial<PlatformConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  const handleSave = useCallback(async () => {
    if (!platformType) return;
    const fullConfig: PlatformConfig = {
      name: config.name!, type: platformType, host: config.host!, port: config.port!,
      username: config.username!, password: config.password!, verify_ssl: config.verify_ssl ?? true,
    };
    addPlatformMutation.mutate(fullConfig, {
      onSuccess: () => {
        onComplete();
        setCurrentStep(0); setPlatformType(null); setConfig({ verify_ssl: true });
        setSyncInterval('60'); setSyncScope('all');
      },
    });
  }, [platformType, config, addPlatformMutation, onComplete]);

  const handleNext = useCallback(() => { if (currentStep < 3) setCurrentStep((p) => p + 1); }, [currentStep]);
  const handleBack = useCallback(() => { if (currentStep > 0) setCurrentStep((p) => p - 1); }, [currentStep]);

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Add platform wizard">
      <div className="w-full max-w-lg mx-4 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)] shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Add Platform</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-[var(--color-bg-tertiary)] transition-colors" aria-label="Close wizard">
            <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div className="px-4 pt-4"><StepIndicator currentStep={currentStep} totalSteps={4} /></div>
        <div className="p-4">
          {currentStep === 0 && <StepSelectType selected={platformType} onSelect={setPlatformType} onNext={handleNext} onBack={handleBack} isFirst={true} isLast={false} />}
          {currentStep === 1 && <StepConnectionConfig config={config} onChange={handleConfigChange} onNext={handleNext} onBack={handleBack} isFirst={false} isLast={false} />}
          {currentStep === 2 && <StepSyncOptions syncInterval={syncInterval} syncScope={syncScope} onIntervalChange={setSyncInterval} onScopeChange={setSyncScope} onNext={handleNext} onBack={handleBack} isFirst={false} isLast={false} />}
          {currentStep === 3 && <StepConfirm config={config} syncInterval={syncInterval} syncScope={syncScope} onSave={handleSave} onBack={handleBack} isFirst={false} isLast={true} isSaving={addPlatformMutation.isPending} />}
        </div>
        {addPlatformMutation.error && (
          <div className="px-4 pb-4">
            <div className="p-3 bg-red-900/20 rounded-lg border border-red-800/30">
              <p className="text-sm text-[var(--color-danger)]">{addPlatformMutation.error.message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
