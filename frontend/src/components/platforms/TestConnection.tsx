import React from 'react';
import { cn } from '../../lib/utils';
import { formatBytes } from '../../lib/utils';
import type { TestResult } from '../../types/platform';

interface TestConnectionProps {
  isLoading: boolean;
  result: TestResult | null;
  error: string | null;
  onRetry: () => void;
}

/**
 * Loading spinner for connection test
 */
function TestingSpinner(): React.JSX.Element {
  return (
    <div
      className="flex flex-col items-center justify-center py-8"
      role="status"
      aria-label="Testing connection"
    >
      <div className="relative w-12 h-12 mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-[var(--color-border)]" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--color-accent)] animate-spin" />
      </div>
      <p className="text-[var(--color-text-secondary)] text-sm">
        Testing connection...
      </p>
    </div>
  );
}

/**
 * Success result display
 */
function SuccessResult({ result }: { result: TestResult }): React.JSX.Element {
  return (
    <div className="space-y-4">
      {/* Success header */}
      <div className="flex items-center gap-3 p-3 bg-green-900/20 rounded-lg border border-green-800/30">
        <svg
          className="w-5 h-5 text-[var(--color-success)] flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
        <span className="text-[var(--color-success)] text-sm font-medium">
          Connection successful
        </span>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-3">
        <DetailCard label="Version" value={result.version} />
        <DetailCard label="Latency" value={`${result.latency_ms}ms`} />
        {result.details?.total_vms !== undefined && (
          <DetailCard label="VMs" value={String(result.details.total_vms)} />
        )}
        {result.details?.total_hosts !== undefined && (
          <DetailCard
            label="Hosts"
            value={String(result.details.total_hosts)}
          />
        )}
        {result.details?.total_storage !== undefined && (
          <DetailCard
            label="Storage"
            value={formatBytes(Number(result.details.total_storage))}
          />
        )}
      </div>
    </div>
  );
}

/**
 * Individual detail card
 */
function DetailCard({
  label,
  value,
}: {
  label: string;
  value: string;
}): React.JSX.Element {
  return (
    <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-3">
      <div className="text-xs text-[var(--color-text-secondary)] mb-1">
        {label}
      </div>
      <div className="text-sm text-[var(--color-text-primary)] font-medium">
        {value}
      </div>
    </div>
  );
}

/**
 * Error result display
 */
function ErrorResult({
  error,
  onRetry,
}: {
  error: string;
  onRetry: () => void;
}): React.JSX.Element {
  return (
    <div className="space-y-4">
      {/* Error header */}
      <div className="flex items-start gap-3 p-3 bg-red-900/20 rounded-lg border border-red-800/30">
        <svg
          className="w-5 h-5 text-[var(--color-danger)] flex-shrink-0 mt-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <div>
          <p className="text-[var(--color-danger)] text-sm font-medium">
            Connection failed
          </p>
          <p className="text-[var(--color-text-secondary)] text-xs mt-1">
            {error}
          </p>
        </div>
      </div>

      <button
        onClick={onRetry}
        className={cn(
          'w-full py-2 px-4 rounded-lg text-sm font-medium',
          'bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)]',
          'hover:bg-[var(--color-border)] transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]'
        )}
        aria-label="Retry connection test"
      >
        Retry
      </button>
    </div>
  );
}

/**
 * Test connection component showing test progress and results
 */
export default function TestConnection({
  isLoading,
  result,
  error,
  onRetry,
}: TestConnectionProps): React.JSX.Element {
  if (isLoading) {
    return <TestingSpinner />;
  }

  if (error) {
    return <ErrorResult error={error} onRetry={onRetry} />;
  }

  if (result) {
    return result.success ? (
      <SuccessResult result={result} />
    ) : (
      <ErrorResult
        error={result.error || 'Unknown error occurred'}
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="text-center py-8 text-[var(--color-text-secondary)] text-sm">
      Click &quot;Test Connection&quot; to verify platform connectivity
    </div>
  );
}
