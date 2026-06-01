import React, { useState, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { formatDuration } from '../../lib/utils';
import { usePlatforms, useVMs, usePlanMigration, useExecuteMigration, useMigrationStatus } from '../../lib/queries';
import { useMigrationStore } from '../../lib/stores';
import type { Platform, Device, MigrationPlan, MigrationExecution } from '../../types/platform';

interface MigrationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

function StepIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }): React.JSX.Element {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: totalSteps }, (_, i) => (
        <React.Fragment key={i}>
          <div className={cn('w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium', i < currentStep ? 'bg-[var(--color-accent)] text-[var(--color-bg-primary)]' : i === currentStep ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border-2 border-[var(--color-accent)]' : 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]')} aria-label={'Step ' + (i + 1)}>
            {i < currentStep ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            ) : i + 1}
          </div>
          {i < totalSteps - 1 && <div className={cn('w-12 h-0.5', i < currentStep ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-border)]')} />}
        </React.Fragment>
      ))}
    </div>
  );
}

function StepSelectVM({ selectedVM, onSelect, onNext, isFirst, isLast }: {
  selectedVM: Device | null; onSelect: (vm: Device) => void;
  onNext: () => void; isFirst: boolean; isLast: boolean;
}): React.JSX.Element {
  const { data: vms, isLoading, error } = useVMs();
  const [search, setSearch] = useState('');

  const filteredVMs = vms?.filter((vm) => vm.name.toLowerCase().includes(search.toLowerCase())) || [];

  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Select Source VM</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Choose a virtual machine to migrate</p>
      <div className="space-y-4">
        <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search VMs..." className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:outline-none focus:border-[var(--color-accent)]" aria-label="Search virtual machines" />
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <p className="text-sm text-[var(--color-danger)] text-center py-4">{error.message}</p>
        ) : filteredVMs.length === 0 ? (
          <p className="text-sm text-[var(--color-text-secondary)] text-center py-8">No virtual machines found</p>
        ) : (
          <div className="max-h-60 overflow-y-auto space-y-2">
            {filteredVMs.map((vm) => (
              <button key={vm.id} onClick={() => onSelect(vm)} className={cn('w-full p-3 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', selectedVM?.id === vm.id ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10' : 'border-[var(--color-border)] bg-[var(--color-bg-tertiary)] hover:border-[var(--color-accent)]/50')} aria-label={'Select ' + vm.name} aria-pressed={selectedVM?.id === vm.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-[var(--color-text-primary)]">{vm.name}</div>
                    <div className="text-xs text-[var(--color-text-secondary)]">{vm.properties?.os || 'Unknown OS'}</div>
                  </div>
                  <span className={cn('text-xs px-2 py-0.5 rounded', vm.status === 'running' ? 'bg-green-900/30 text-[var(--color-success)]' : 'bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)]')}>{vm.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="flex justify-end mt-6 pt-4 border-t border-[var(--color-border)]">
        <button onClick={onNext} disabled={!selectedVM} className={cn('px-6 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', !selectedVM ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Continue to next step">
          Next
        </button>
      </div>
    </div>
  );
}

function StepSelectTarget({ sourceVM, selectedPlatform, onSelect, onNext, onBack }: {
  sourceVM: Device | null; selectedPlatform: Platform | null; onSelect: (p: Platform) => void;
  onNext: () => void; onBack: () => void;
}): React.JSX.Element {
  const { data: platforms, isLoading } = usePlatforms();
  const availablePlatforms = platforms?.filter((p) => p.id !== sourceVM?.platform_id && p.status === 'connected') || [];

  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Select Target Platform</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Choose the destination platform for migration</p>
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : availablePlatforms.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-[var(--color-text-secondary)]">No connected platforms available as migration targets</p>
        </div>
      ) : (
        <div className="space-y-3">
          {availablePlatforms.map((platform) => (
            <button key={platform.id} onClick={() => onSelect(platform)} className={cn('w-full p-4 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', selectedPlatform?.id === platform.id ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10' : 'border-[var(--color-border)] bg-[var(--color-bg-tertiary)] hover:border-[var(--color-accent)]/50')} aria-label={'Select ' + platform.name + ' as target'} aria-pressed={selectedPlatform?.id === platform.id}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-[var(--color-text-primary)]">{platform.name}</div>
                  <div className="text-xs text-[var(--color-text-secondary)]">{platform.type} - {platform.host}:{platform.port}</div>
                </div>
                <div className="text-xs text-[var(--color-text-secondary)]">{platform.device_count.vms} VMs</div>
              </div>
            </button>
          ))}
        </div>
      )}
      <div className="flex justify-between mt-6 pt-4 border-t border-[var(--color-border)]">
        <button onClick={onBack} className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Go back">Back</button>
        <button onClick={onNext} disabled={!selectedPlatform} className={cn('px-6 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', !selectedPlatform ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Generate migration plan">
          Generate Plan
        </button>
      </div>
    </div>
  );
}

function StepMigrationPlan({ plan, onDryRun, onExecute, onBack, isExecuting }: {
  plan: MigrationPlan | null; onDryRun: () => void; onExecute: () => void;
  onBack: () => void; isExecuting: boolean;
}): React.JSX.Element {
  if (!plan) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-[var(--color-text-secondary)]">No migration plan generated</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Migration Plan</h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-4">Review the migration plan before executing</p>
      <div className="space-y-4">
        <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-[var(--color-text-secondary)]">Source VM</span>
            <span className="text-[var(--color-text-primary)] font-medium">{plan.source_vm.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[var(--color-text-secondary)]">Target</span>
            <span className="text-[var(--color-text-primary)] font-medium">{plan.target_platform}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[var(--color-text-secondary)]">Tool</span>
            <span className="text-[var(--color-text-primary)] font-medium">{plan.tool.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[var(--color-text-secondary)]">Estimated Time</span>
            <span className="text-[var(--color-text-primary)] font-medium">{formatDuration(plan.estimated_time_seconds)}</span>
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Steps</h4>
          <div className="space-y-2">
            {plan.steps.map((step) => (
              <div key={step.step} className="flex items-start gap-3 p-2 bg-[var(--color-bg-primary)] rounded">
                <div className="w-6 h-6 rounded-full bg-[var(--color-accent)]/20 text-[var(--color-accent)] flex items-center justify-center text-xs font-medium flex-shrink-0">{step.step}</div>
                <div>
                  <div className="text-sm text-[var(--color-text-primary)]">{step.description}</div>
                  <div className="text-xs text-[var(--color-text-secondary)]">Est. {formatDuration(step.estimated_seconds)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        {plan.risks.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-[var(--color-warning)] mb-2">Risks</h4>
            <ul className="space-y-1">
              {plan.risks.map((risk, i) => (
                <li key={i} className="text-xs text-[var(--color-text-secondary)] flex items-start gap-2">
                  <svg className="w-4 h-4 text-[var(--color-warning)] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
                  {risk}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <div className="flex justify-between mt-6 pt-4 border-t border-[var(--color-border)]">
        <button onClick={onBack} className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Go back">Back</button>
        <div className="flex gap-3">
          <button onClick={onDryRun} disabled={isExecuting} className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] hover:bg-[var(--color-border)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Run dry run">Dry Run</button>
          <button onClick={onExecute} disabled={isExecuting} className={cn('px-6 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', isExecuting ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Execute migration">
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
        </div>
      </div>
    </div>
  );
}

function StepExecution({ executionId, onComplete, onBack }: {
  executionId: string | null; onComplete: () => void; onBack: () => void;
}): React.JSX.Element {
  const { data: execution, isLoading } = useMigrationStatus(executionId, !!executionId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-[var(--color-text-secondary)]">No execution data available</p>
      </div>
    );
  }

  const progress = execution.plan.steps.length > 0 ? (execution.current_step / execution.plan.steps.length) * 100 : 0;

  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">Migration Progress</h3>
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-[var(--color-text-secondary)]">Progress</span>
            <span className="text-[var(--color-text-primary)]">{Math.round(progress)}%</span>
          </div>
          <div className="w-full h-2 bg-[var(--color-bg-tertiary)] rounded-full overflow-hidden">
            <div className={cn('h-full transition-all duration-500', execution.status === 'failed' ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-accent)]')} style={{ width: progress + '%' }} />
          </div>
        </div>
        <div className="space-y-2">
          {execution.plan.steps.map((step) => (
            <div key={step.step} className={cn('flex items-center gap-3 p-2 rounded', step.step < execution.current_step ? 'bg-green-900/10' : step.step === execution.current_step ? 'bg-[var(--color-accent)]/10' : 'bg-[var(--color-bg-tertiary)]')}>
              <div className={cn('w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium', step.step < execution.current_step ? 'bg-[var(--color-success)] text-[var(--color-bg-primary)]' : step.step === execution.current_step ? 'bg-[var(--color-accent)] text-[var(--color-bg-primary)]' : 'bg-[var(--color-border)] text-[var(--color-text-secondary)]')}>
                {step.step < execution.current_step ? (
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                ) : step.step}
              </div>
              <span className={cn('text-sm', step.step <= execution.current_step ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)]')}>{step.description}</span>
            </div>
          ))}
        </div>
        {execution.status === 'failed' && execution.error && (
          <div className="p-3 bg-red-900/20 rounded-lg border border-red-800/30">
            <p className="text-sm text-[var(--color-danger)]">{execution.error}</p>
          </div>
        )}
        {execution.status === 'completed' && (
          <div className="p-3 bg-green-900/20 rounded-lg border border-green-800/30">
            <p className="text-sm text-[var(--color-success)]">Migration completed successfully</p>
          </div>
        )}
      </div>
      <div className="flex justify-between mt-6 pt-4 border-t border-[var(--color-border)]">
        <button onClick={onBack} className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]" aria-label="Go back">Back</button>
        <button onClick={onComplete} disabled={execution.status !== 'completed' && execution.status !== 'failed'} className={cn('px-6 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]', execution.status !== 'completed' && execution.status !== 'failed' ? 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)] cursor-not-allowed' : 'bg-[var(--color-accent)] text-[var(--color-bg-primary)] hover:bg-[var(--color-accent)]/90')} aria-label="Finish">
          Finish
        </button>
      </div>
    </div>
  );
}

export default function MigrationWizard({ isOpen, onClose, onComplete }: MigrationWizardProps): React.JSX.Element | null {
  const [currentStep, setCurrentStep] = useState(0);
  const { selectedVM, setSelectedVM, targetPlatform, setTargetPlatform, currentPlan, setCurrentPlan, execution, setExecution, reset } = useMigrationStore();
  const planMutation = usePlanMigration();
  const executeMutation = useExecuteMigration();
  const [executionId, setExecutionId] = useState<string | null>(null);

  const handleGeneratePlan = useCallback(() => {
    if (!selectedVM || !targetPlatform) return;
    planMutation.mutate(
      { vmId: selectedVM.id, targetPlatformId: targetPlatform.id },
      { onSuccess: (plan) => { setCurrentPlan(plan); setCurrentStep(2); } }
    );
  }, [selectedVM, targetPlatform, planMutation, setCurrentPlan]);

  const handleExecute = useCallback(() => {
    if (!currentPlan) return;
    executeMutation.mutate(currentPlan.id, {
      onSuccess: (exec) => {
        setExecution(exec);
        setExecutionId(exec.id);
        setCurrentStep(3);
      },
    });
  }, [currentPlan, executeMutation, setExecution]);

  const handleDryRun = useCallback(() => {
    // Dry run uses the same execute path but in dry-run mode
    // For now, just show the plan as-is
    setCurrentStep(3);
  }, []);

  const handleClose = useCallback(() => {
    reset();
    setCurrentStep(0);
    setExecutionId(null);
    onClose();
  }, [reset, onClose]);

  const handleComplete = useCallback(() => {
    reset();
    setCurrentStep(0);
    setExecutionId(null);
    onComplete();
  }, [reset, onComplete]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Migration wizard">
      <div className="w-full max-w-2xl mx-4 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border)] shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Migrate Virtual Machine</h2>
          <button onClick={handleClose} className="p-1 rounded-lg hover:bg-[var(--color-bg-tertiary)] transition-colors" aria-label="Close wizard">
            <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div className="px-4 pt-4"><StepIndicator currentStep={currentStep} totalSteps={4} /></div>
        <div className="p-4">
          {currentStep === 0 && (
            <StepSelectVM selectedVM={selectedVM} onSelect={setSelectedVM} onNext={() => setCurrentStep(1)} isFirst={true} isLast={false} />
          )}
          {currentStep === 1 && (
            <StepSelectTarget sourceVM={selectedVM} selectedPlatform={targetPlatform} onSelect={setTargetPlatform} onNext={handleGeneratePlan} onBack={() => setCurrentStep(0)} />
          )}
          {currentStep === 2 && (
            <StepMigrationPlan plan={currentPlan} onDryRun={handleDryRun} onExecute={handleExecute} onBack={() => setCurrentStep(1)} isExecuting={executeMutation.isPending} />
          )}
          {currentStep === 3 && (
            <StepExecution executionId={executionId} onComplete={handleComplete} onBack={() => setCurrentStep(2)} />
          )}
        </div>
        {(planMutation.error || executeMutation.error) && (
          <div className="px-4 pb-4">
            <div className="p-3 bg-red-900/20 rounded-lg border border-red-800/30">
              <p className="text-sm text-[var(--color-danger)]">{planMutation.error?.message || executeMutation.error?.message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
